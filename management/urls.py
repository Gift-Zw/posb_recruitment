"""
URL configuration for management portal (HR employees only).
All URLs are prefixed with /management/
"""
from django.urls import path, include
from accounts.views import ManagementLoginView

app_name = "management"

from jobs.views import ManagementDashboardView

urlpatterns = [
    # Management login (must be first, before other routes)
    path('login/', ManagementLoginView.as_view(), name='login'),
    
    # Dashboard (default after login)
    path('', ManagementDashboardView.as_view(), name='dashboard'),
    
    # Job management routes
    path('jobs/', include('jobs.management_urls')),
    
    # Applications management routes
    path('applications/', include('applications.management_urls')),
    
    # User management routes
    path('users/', include('accounts.management_urls')),
    
    # Shortlisting management routes
    path('shortlisting/', include('shortlisting.management_urls')),
    
]
