"""
Management URL configuration for applications app (HR only).
URLs are accessed via /management/applications/
"""
from django.urls import path
from . import management_views

app_name = "applications_management"

urlpatterns = [
    path('', management_views.ApplicationManagementListView.as_view(), name='list'),
    path('<int:pk>/', management_views.ApplicationManagementDetailView.as_view(), name='detail'),
    path('<int:pk>/review/', management_views.ReviewSingleApplicationView.as_view(), name='review-single'),
    path('<int:pk>/upload/', management_views.UploadSingleApplicationView.as_view(), name='upload-single'),
    path('upload/bulk/', management_views.UploadBulkApplicationsView.as_view(), name='upload-bulk'),
    path('applicant/<int:pk>/', management_views.ApplicantProfileManagementView.as_view(), name='applicant-profile'),
]
