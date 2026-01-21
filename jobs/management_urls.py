"""
Management URL configuration for jobs app (HR only).
URLs are accessed via /management/jobs/
"""
from django.urls import path
from . import views

app_name = "jobs_management"

urlpatterns = [
    path('', views.JobAdvertListView.as_view(), name='list'),
    path('create/', views.JobAdvertCreateView.as_view(), name='advert-create'),
    path('<int:pk>/', views.JobAdvertDetailView.as_view(), name='advert-detail'),
    path('<int:pk>/edit/', views.JobAdvertUpdateView.as_view(), name='advert-edit'),
    path('categories/', views.JobCategoryListView.as_view(), name='category-list'),
    path('categories/create/', views.JobCategoryCreateView.as_view(), name='category-create'),
    path('skills/', views.SkillListView.as_view(), name='skill-list'),
    path('skills/create/', views.SkillCreateView.as_view(), name='skill-create'),
]
