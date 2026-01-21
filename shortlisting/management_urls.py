"""
Management URL configuration for shortlisting app (HR only).
URLs are accessed via /management/shortlisting/
"""
from django.urls import path
from . import views

app_name = "shortlisting_management"

urlpatterns = [
    path('', views.ShortlistingRunListView.as_view(), name='list'),
    path('trigger/<int:job_id>/', views.TriggerShortlistingView.as_view(), name='trigger'),
]
