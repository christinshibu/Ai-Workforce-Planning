# AI-Driven Hospital Workforce Planning & Shift Optimization (Django)

A professional full-stack Django platform that predicts patient demand, translates it to staffing demand, and generates optimized shift rosters with alerts.

## Core Capabilities
- Authentication and role-based authorization (`WorkforceManager` vs viewer).
- CSV ingestion pipeline for historical workload data.
- ML forecasting (scikit-learn linear regression) for admissions and bed occupancy.
- Constraint-based schedule optimization (Google OR-Tools CP-SAT).
- Real-time alerts over WebSocket (Django Channels).
- Responsive dashboard UX for operations teams.

## Technology Stack
- **Backend:** Django + Channels + ORM
- **Database:** SQLite (default, can switch to PostgreSQL)
- **ML/AI:** Pandas + scikit-learn
- **Optimization:** OR-Tools CP-SAT solver
- **Frontend:** Django templates + CSS + vanilla JS WebSocket client

## Project Structure
- `his_workforce/` → Django project config (ASGI/WSGI/settings)
- `planner/` → workforce planning app (models, services, views, templates)
- `data/dummy_hospital_workload.csv` → ready-to-upload sample dataset

## CSV Schema
The upload endpoint expects columns:

`department,date,shift,patient_admissions,opd_visits,bed_occupancy_rate,emergency_cases`

`shift` must be one of: `morning`, `evening`, `night`.

## Quick Start (No Docker Required)
This project is intentionally designed to run directly with Python virtual environments. Docker is optional and **not required**.

### One-command local startup
```bash
bash scripts/start_local.sh
```

The script creates `.venv` (if missing), installs dependencies, runs migrations, seeds demo data, and starts Daphne.

## Step-by-Step Build & Run Guide
1. **Create environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run migrations**
   ```bash
   python manage.py migrate
   ```
4. **Seed demo users and staff**
   ```bash
   python manage.py seed_demo
   ```
5. **Run ASGI server for WebSockets + HTTP**
   ```bash
   daphne -b 0.0.0.0 -p 8000 his_workforce.asgi:application
   ```
6. **Login credentials**
   - Manager: `manager / manager123`
   - Viewer: `viewer / viewer123`
7. **Upload CSV**
   - Use `data/dummy_hospital_workload.csv` at `/upload/`.
8. **Generate plan**
   - Go to `/forecast/` and submit horizon (e.g., 14 days).
   - The app generates forecasts + next-day optimized schedule.
9. **Monitor outputs**
   - Dashboard: KPI cards + forecast preview.
   - Schedules: assignment table by department/shift.
   - Alerts: real-time plus historical alert list.

## Additional Professional Specifications Implemented
- **Security baseline:** Django auth, CSRF, permission-protected operations.
- **Operational resilience:** alerts raised for infeasible optimization or understaffing.
- **Scalability path:** Channel layer pluggable to Redis in production.
- **Data quality gates:** required schema validation during CSV ingestion.
- **Clinical realism constraints:** one shift per day per staff, role-mix requirements.
- **Extensibility:** service layer isolated for future model upgrades (Prophet/LSTM/XGBoost).

## Suggested Next Enhancements
- Add leave management and holiday calendars.
- Add fairness scoring dashboards per staff member.
- Add what-if scenario simulation (flu season surge).
- Integrate PostgreSQL + Redis + Celery for enterprise deployment.
- Add REST API + React frontend if multi-client integration is needed.
