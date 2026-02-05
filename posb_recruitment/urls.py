"""
URL configuration for POSB Recruitment Portal (server-rendered views).
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from jobs.views import JobListView, HomeView
from accounts.views import ProfileView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Default landing -> home page
    path('', HomeView.as_view(), name='home'),
    
    # Web routes (applicant portal)
    path('auth/', include('accounts.urls')),
    path('applicant-profile/', ProfileView.as_view(), name='applicant-profile'),
    path('jobs/', include('jobs.urls')),
    path('applications/', include('applications.urls')),
    
    # Management portal (HR employees only) - separate from applicant portal
    path('management/', include('management.urls')),

    # External API (D365 job postings)
    path('api/v1/', include('integrations.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
