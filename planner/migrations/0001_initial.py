from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('min_staff_per_shift', models.PositiveIntegerField(default=2)),
            ],
        ),
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_acknowledged', models.BooleanField(default=False)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='planner.department')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Staff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=150)),
                ('role', models.CharField(choices=[('doctor', 'Doctor'), ('nurse', 'Nurse'), ('support', 'Support Staff')], max_length=20)),
                ('max_hours_per_week', models.PositiveIntegerField(default=48)),
                ('skill_level', models.PositiveIntegerField(default=3)),
                ('is_active', models.BooleanField(default=True)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='planner.department')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ForecastResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('forecast_date', models.DateField()),
                ('predicted_patients', models.FloatField()),
                ('predicted_bed_occupancy', models.FloatField()),
                ('required_doctors', models.PositiveIntegerField()),
                ('required_nurses', models.PositiveIntegerField()),
                ('required_support', models.PositiveIntegerField()),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='planner.department')),
            ],
            options={'ordering': ['-generated_at']},
        ),
        migrations.CreateModel(
            name='WorkloadRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('shift', models.CharField(choices=[('morning', 'Morning'), ('evening', 'Evening'), ('night', 'Night')], max_length=20)),
                ('patient_admissions', models.PositiveIntegerField(default=0)),
                ('opd_visits', models.PositiveIntegerField(default=0)),
                ('bed_occupancy_rate', models.FloatField(default=0)),
                ('emergency_cases', models.PositiveIntegerField(default=0)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='planner.department')),
            ],
            options={'ordering': ['-date'], 'unique_together': {('department', 'date', 'shift')}},
        ),
        migrations.CreateModel(
            name='ShiftSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('shift', models.CharField(choices=[('morning', 'Morning'), ('evening', 'Evening'), ('night', 'Night')], max_length=20)),
                ('assigned_hours', models.PositiveIntegerField(default=8)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='planner.department')),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='planner.staff')),
            ],
            options={'unique_together': {('staff', 'date', 'shift')}},
        ),
    ]
