"""
URL configuration for shortlisting (HR views).
"""
from django.urls import path
from . import views

app_name = "shortlisting"

urlpatterns = [
    path("", views.ShortlistingRunListView.as_view(), name="list"),
    path("trigger/<int:job_id>/", views.TriggerShortlistingView.as_view(), name="trigger"),
]
