from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views import View
from django.views.generic import FormView, ListView, TemplateView

from .forms import CSVUploadForm, ForecastForm
from .models import Alert, Department, ForecastResult, ShiftSchedule, WorkloadRecord
from .services import build_schedule, generate_forecast, ingest_csv


class HomeView(TemplateView):
    template_name = 'planner/home.html'


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'planner/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        context.update(
            {
                'department_count': Department.objects.count(),
                'workload_count': WorkloadRecord.objects.count(),
                'forecast_count': ForecastResult.objects.count(),
                'today_assignments': ShiftSchedule.objects.filter(date=today).count(),
                'unread_alerts': Alert.objects.filter(is_acknowledged=False).count(),
                'latest_alerts': Alert.objects.select_related('department')[:8],
                'forecast_preview': ForecastResult.objects.select_related('department')[:10],
            }
        )
        return context


class CSVUploadView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = 'planner/upload.html'
    permission_required = 'planner.add_workloadrecord'
    form_class = CSVUploadForm

    def form_valid(self, form):
        uploaded = form.cleaned_data['csv_file']
        try:
            result = ingest_csv(uploaded.read())
        except ValueError as exc:
            form.add_error('csv_file', str(exc))
            return self.form_invalid(form)

        messages.success(
            self.request,
            f"CSV processed successfully. Rows={result['rows_processed']}, new records={result['new_records']}.",
        )
        return redirect('planner:dashboard')


class RunForecastView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = 'planner/forecast.html'
    permission_required = 'planner.add_forecastresult'
    form_class = ForecastForm

    def form_valid(self, form):
        horizon_days = form.cleaned_data['horizon_days']
        forecasts = generate_forecast(horizon_days=horizon_days)
        target_date = timezone.now().date() + timedelta(days=1)
        schedule = build_schedule(target_date=target_date)

        if not forecasts:
            messages.warning(self.request, 'Not enough workload data to produce forecasts yet.')
        else:
            messages.success(
                self.request,
                f'Generated {len(forecasts)} forecast entries and {len(schedule)} schedule assignments.',
            )
            _broadcast_alerts()
        return redirect('planner:dashboard')


class ScheduleView(LoginRequiredMixin, ListView):
    template_name = 'planner/schedule.html'
    context_object_name = 'assignments'

    def get_queryset(self):
        target_date = self.request.GET.get('date')
        qs = ShiftSchedule.objects.select_related('staff', 'department').order_by('department__name', 'shift')
        if target_date:
            return qs.filter(date=target_date)
        return qs.filter(date=timezone.now().date() + timedelta(days=1))


class AlertListView(LoginRequiredMixin, ListView):
    template_name = 'planner/alerts.html'
    context_object_name = 'alerts'
    queryset = Alert.objects.select_related('department')


def alerts_api(request):
    alerts = list(
        Alert.objects.select_related('department').values(
            'id', 'department__name', 'message', 'severity', 'created_at', 'is_acknowledged'
        )[:20]
    )
    return JsonResponse({'alerts': alerts})


def _broadcast_alerts() -> None:
    layer = get_channel_layer()
    payload = {
        'type': 'alert_message',
        'payload': {
            'title': 'Workforce plan updated',
            'message': 'Forecast and schedule have been regenerated. Check latest alerts dashboard.',
            'timestamp': timezone.now().isoformat(),
        },
    }
    async_to_sync(layer.group_send)('hospital_alerts', payload)
