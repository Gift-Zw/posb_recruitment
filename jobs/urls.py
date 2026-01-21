"""
URL configuration for jobs app (applicant portal - server-rendered views).
HR management URLs are in management_urls.py (accessed via /management/jobs/).
"""
from django.urls import path
from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.JobListView.as_view(), name="list"),
    path("faqs/", views.FAQsView.as_view(), name="faqs"),
    path("adverts/<int:pk>/", views.JobDetailView.as_view(), name="detail"),
]
