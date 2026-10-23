from django.urls import path
from .views import export_report_csv, reports_view

urlpatterns = [
    path('', reports_view, name='reports'),
    path('export/', export_report_csv, name='export_report_csv'),
]
