"""
URL configuration for application submissions (server-rendered).
"""
from django.urls import path
from . import views

app_name = "applications"

urlpatterns = [
    path("", views.ApplicationListView.as_view(), name="list"),
    path("<int:pk>/", views.ApplicationDetailView.as_view(), name="detail"),
    path("apply/<int:job_id>/", views.ApplyView.as_view(), name="apply"),
]
