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
    path('<int:pk>/applications/', views.JobApplicationsListView.as_view(), name='job-applications'),
    path('skills/', views.SkillListView.as_view(), name='skill-list'),
    path('skills/create/', views.SkillCreateView.as_view(), name='skill-create'),
]
