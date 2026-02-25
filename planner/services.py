import io
from collections import defaultdict
from datetime import timedelta

import pandas as pd
from django.db import transaction
from django.utils import timezone
from ortools.sat.python import cp_model
from sklearn.linear_model import LinearRegression

from .models import Alert, Department, ForecastResult, ShiftSchedule, Staff, WorkloadRecord


REQUIRED_COLUMNS = {
    'department',
    'date',
    'shift',
    'patient_admissions',
    'opd_visits',
    'bed_occupancy_rate',
    'emergency_cases',
}


def ingest_csv(content: bytes) -> dict[str, int]:
    frame = pd.read_csv(io.BytesIO(content))
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f'Missing required columns: {", ".join(sorted(missing))}')

    frame['date'] = pd.to_datetime(frame['date']).dt.date
    created_records = 0

    with transaction.atomic():
        for _, row in frame.iterrows():
            dept, _ = Department.objects.get_or_create(name=row['department'])
            _, created = WorkloadRecord.objects.update_or_create(
                department=dept,
                date=row['date'],
                shift=row['shift'],
                defaults={
                    'patient_admissions': int(row['patient_admissions']),
                    'opd_visits': int(row['opd_visits']),
                    'bed_occupancy_rate': float(row['bed_occupancy_rate']),
                    'emergency_cases': int(row['emergency_cases']),
                },
            )
            if created:
                created_records += 1
    return {'rows_processed': len(frame), 'new_records': created_records}


def generate_forecast(horizon_days: int = 14) -> list[ForecastResult]:
    ForecastResult.objects.all().delete()
    outputs: list[ForecastResult] = []

    for dept in Department.objects.all():
        history = list(
            WorkloadRecord.objects.filter(department=dept).order_by('date').values(
                'date', 'patient_admissions', 'bed_occupancy_rate', 'opd_visits', 'emergency_cases'
            )
        )
        if len(history) < 7:
            continue

        frame = pd.DataFrame(history)
        frame['ordinal'] = pd.to_datetime(frame['date']).map(pd.Timestamp.toordinal)

        x = frame[['ordinal', 'opd_visits', 'emergency_cases']]
        y_patients = frame['patient_admissions']
        y_bed = frame['bed_occupancy_rate']

        model_patients = LinearRegression().fit(x, y_patients)
        model_bed = LinearRegression().fit(x, y_bed)

        latest_date = max(item['date'] for item in history)
        rolling_opd = float(frame['opd_visits'].tail(7).mean())
        rolling_emergency = float(frame['emergency_cases'].tail(7).mean())

        for offset in range(1, horizon_days + 1):
            f_date = latest_date + timedelta(days=offset)
            features = [[f_date.toordinal(), rolling_opd, rolling_emergency]]
            predicted_patients = max(1.0, float(model_patients.predict(features)[0]))
            predicted_bed = min(100.0, max(1.0, float(model_bed.predict(features)[0])))

            doctors = max(1, round(predicted_patients / 18))
            nurses = max(1, round(predicted_patients / 8))
            support = max(1, round(predicted_patients / 12))

            outputs.append(
                ForecastResult.objects.create(
                    department=dept,
                    forecast_date=f_date,
                    predicted_patients=predicted_patients,
                    predicted_bed_occupancy=predicted_bed,
                    required_doctors=doctors,
                    required_nurses=nurses,
                    required_support=support,
                )
            )
    return outputs


def build_schedule(target_date=None) -> list[ShiftSchedule]:
    target_date = target_date or (timezone.now().date() + timedelta(days=1))
    ShiftSchedule.objects.filter(date=target_date).delete()

    daily_requirements: dict[int, dict[str, int]] = defaultdict(lambda: {'doctor': 1, 'nurse': 2, 'support': 1})
    for forecast in ForecastResult.objects.filter(forecast_date=target_date):
        daily_requirements[forecast.department_id] = {
            'doctor': forecast.required_doctors,
            'nurse': forecast.required_nurses,
            'support': forecast.required_support,
        }

    assignments: list[ShiftSchedule] = []
    shifts = ['morning', 'evening', 'night']

    for dept in Department.objects.all():
        staff_pool = list(Staff.objects.filter(department=dept, is_active=True))
        if not staff_pool:
            Alert.objects.create(
                department=dept,
                severity='high',
                message=f'No active staff available for {dept.name} on {target_date}.',
            )
            continue

        model = cp_model.CpModel()
        decision = {}
        for idx, staff in enumerate(staff_pool):
            for shift in shifts:
                decision[(idx, shift)] = model.NewBoolVar(f'assigned_{idx}_{shift}')

        for idx, _staff in enumerate(staff_pool):
            model.Add(sum(decision[(idx, shift)] for shift in shifts) <= 1)

        req = daily_requirements[dept.id]
        for shift in shifts:
            doctors = [decision[(i, shift)] for i, s in enumerate(staff_pool) if s.role == 'doctor']
            nurses = [decision[(i, shift)] for i, s in enumerate(staff_pool) if s.role == 'nurse']
            support = [decision[(i, shift)] for i, s in enumerate(staff_pool) if s.role == 'support']
            if doctors:
                model.Add(sum(doctors) >= min(len(doctors), req['doctor']))
            if nurses:
                model.Add(sum(nurses) >= min(len(nurses), req['nurse']))
            if support:
                model.Add(sum(support) >= min(len(support), req['support']))

        objective_terms = []
        for idx, staff in enumerate(staff_pool):
            for shift in shifts:
                objective_terms.append(decision[(idx, shift)] * staff.skill_level)
        model.Maximize(sum(objective_terms))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 5
        status = solver.Solve(model)

        if status not in {cp_model.OPTIMAL, cp_model.FEASIBLE}:
            Alert.objects.create(
                department=dept,
                severity='high',
                message=f'Unable to produce a feasible schedule for {dept.name} on {target_date}.',
            )
            continue

        for idx, staff in enumerate(staff_pool):
            for shift in shifts:
                if solver.Value(decision[(idx, shift)]) == 1:
                    assignments.append(
                        ShiftSchedule.objects.create(
                            department=dept, staff=staff, date=target_date, shift=shift
                        )
                    )

    evaluate_alerts(target_date)
    return assignments


def evaluate_alerts(target_date=None) -> None:
    target_date = target_date or timezone.now().date()
    for dept in Department.objects.all():
        assigned = ShiftSchedule.objects.filter(department=dept, date=target_date).count()
        min_required = dept.min_staff_per_shift * 3
        if assigned < min_required:
            Alert.objects.create(
                department=dept,
                severity='medium',
                message=(
                    f'Potential understaffing in {dept.name} for {target_date}. '
                    f'Assigned={assigned}, required minimum={min_required}.'
                ),
            )
