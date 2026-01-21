"""
URL configuration for integrations (ERP exports).
"""
from django.urls import path
from . import views

app_name = "integrations"

urlpatterns = [
    path("exports/", views.ERPExportListView.as_view(), name="exports"),
    path("exports/trigger/<int:run_id>/", views.TriggerExportView.as_view(), name="export-trigger"),
]
