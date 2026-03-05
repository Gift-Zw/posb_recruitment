"""
Management URL configuration for jobs app (HR only).
URLs are accessed via /management/jobs/
"""
from django.urls import path
from . import views

app_name = "jobs_management"

urlpatterns = [
    path('', views.JobAdvertListView.as_view(), name='list'),
    path('<int:pk>/', views.JobAdvertDetailView.as_view(), name='advert-detail'),
    path('<int:pk>/close/', views.JobAdvertCloseView.as_view(), name='advert-close'),
    path('<int:pk>/reopen/', views.JobAdvertReopenView.as_view(), name='advert-reopen'),
    path('<int:pk>/extend-date/', views.JobAdvertExtendDateView.as_view(), name='advert-extend-date'),
    path('<int:pk>/applications/', views.JobApplicationsListView.as_view(), name='job-applications'),
    path('<int:pk>/push-d365/', views.JobPushAllToD365View.as_view(), name='push-d365'),
    path('<int:pk>/applications/<int:application_id>/push-d365/', views.JobPushSingleToD365View.as_view(), name='push-single-d365'),
    path('skills/', views.SkillListView.as_view(), name='skill-list'),
    path('skills/create/', views.SkillCreateView.as_view(), name='skill-create'),
    # Education Levels
    path('education-levels/', views.EducationLevelListView.as_view(), name='education-level-list'),
    path('education-levels/create/', views.EducationLevelCreateView.as_view(), name='education-level-create'),
    path('education-levels/<int:pk>/edit/', views.EducationLevelUpdateView.as_view(), name='education-level-edit'),
    path('education-levels/<int:pk>/toggle/', views.EducationLevelDeleteView.as_view(), name='education-level-toggle'),
    # Countries
    path('countries/', views.CountryListView.as_view(), name='country-list'),
    path('countries/create/', views.CountryCreateView.as_view(), name='country-create'),
    path('countries/<int:pk>/edit/', views.CountryUpdateView.as_view(), name='country-edit'),
    path('countries/<int:pk>/toggle/', views.CountryToggleView.as_view(), name='country-toggle'),
]
