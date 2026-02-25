from django.urls import path

from . import views

app_name = 'planner'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('upload/', views.CSVUploadView.as_view(), name='upload'),
    path('forecast/', views.RunForecastView.as_view(), name='forecast'),
    path('schedule/', views.ScheduleView.as_view(), name='schedule'),
    path('alerts/', views.AlertListView.as_view(), name='alerts'),
    path('alerts/api/', views.alerts_api, name='alerts_api'),
]
