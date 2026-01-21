"""
Management URL configuration for accounts app (HR only).
URLs are accessed via /management/users/
"""
from django.urls import path
from . import management_views

app_name = "users_management"

urlpatterns = [
    # Employees management
    path('employees/', management_views.EmployeeManagementListView.as_view(), name='employees'),
    path('employees/create/', management_views.UserManagementCreateView.as_view(), name='create'),
    path('employees/<int:pk>/edit/', management_views.UserManagementUpdateView.as_view(), name='edit'),
    path('employees/<int:pk>/toggle-status/', management_views.ToggleUserStatusView.as_view(), name='toggle-status'),
    
    # Applicants management
    path('applicants/', management_views.ApplicantManagementListView.as_view(), name='applicants'),
    path('applicants/<int:pk>/edit/', management_views.UserManagementUpdateView.as_view(), name='applicant-edit'),
    path('applicants/<int:pk>/toggle-status/', management_views.ToggleUserStatusView.as_view(), name='applicant-toggle-status'),
]
