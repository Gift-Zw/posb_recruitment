"""
URL configuration for external integration APIs.
"""
from django.urls import path

from .api_views import vacancies_endpoint

app_name = "integrations_api"

urlpatterns = [
    path("vacancies", vacancies_endpoint, name="vacancies"),
    path("vacancies/", vacancies_endpoint, name="vacancies-slash"),
]
