"""
Management URL configuration for integrations app (HR only).
URLs are accessed via /management/integrations/
"""
from django.urls import path
from . import views

app_name = "integrations_management"

urlpatterns = [
    path('exports/', views.ERPExportListView.as_view(), name='exports'),
    path('exports/trigger/<int:run_id>/', views.TriggerExportView.as_view(), name='export-trigger'),
    
    # API Key Management
    path('api-keys/', views.APIKeyListView.as_view(), name='api-keys'),
    path('api-keys/create/', views.APIKeyCreateView.as_view(), name='api-key-create'),
    path('api-keys/<int:pk>/toggle/', views.APIKeyToggleView.as_view(), name='api-key-toggle'),
]
