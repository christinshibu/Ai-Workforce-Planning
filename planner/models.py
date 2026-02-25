from django.contrib.auth.models import User
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    min_staff_per_shift = models.PositiveIntegerField(default=2)

    def __str__(self) -> str:
        return self.name


class Staff(models.Model):
    ROLE_CHOICES = [
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('support', 'Support Staff'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=150)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    max_hours_per_week = models.PositiveIntegerField(default=48)
    skill_level = models.PositiveIntegerField(default=3)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'{self.full_name} ({self.department.name})'


class WorkloadRecord(models.Model):
    SHIFT_CHOICES = [('morning', 'Morning'), ('evening', 'Evening'), ('night', 'Night')]

    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    date = models.DateField()
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES)
    patient_admissions = models.PositiveIntegerField(default=0)
    opd_visits = models.PositiveIntegerField(default=0)
    bed_occupancy_rate = models.FloatField(default=0)
    emergency_cases = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('department', 'date', 'shift')
        ordering = ['-date']


class ForecastResult(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    forecast_date = models.DateField()
    predicted_patients = models.FloatField()
    predicted_bed_occupancy = models.FloatField()
    required_doctors = models.PositiveIntegerField()
    required_nurses = models.PositiveIntegerField()
    required_support = models.PositiveIntegerField()

    class Meta:
        ordering = ['-generated_at']


class ShiftSchedule(models.Model):
    SHIFT_CHOICES = [('morning', 'Morning'), ('evening', 'Evening'), ('night', 'Night')]

    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.DateField()
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES)
    assigned_hours = models.PositiveIntegerField(default=8)

    class Meta:
        unique_together = ('staff', 'date', 'shift')


class Alert(models.Model):
    SEVERITY_CHOICES = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]

    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_acknowledged = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
