from django.contrib import admin

from .models import Alert, Department, ForecastResult, ShiftSchedule, Staff, WorkloadRecord

admin.site.register(Department)
admin.site.register(Staff)
admin.site.register(WorkloadRecord)
admin.site.register(ForecastResult)
admin.site.register(ShiftSchedule)
admin.site.register(Alert)
