"""
URL configuration for accounts app (server-rendered views).
"""
from django.urls import path
from .views import (
    RegistrationView,
    OTPRequestView,
    OTPVerifyView,
    LoginView,
    LogoutView,
    ProfileView,
    PasswordResetRequestView,
    PasswordResetEmailSentView,
    PasswordResetConfirmView,
)

urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('otp/request/', OTPRequestView.as_view(), name='otp-request'),
    path('otp/verify/', OTPVerifyView.as_view(), name='otp-verify'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Password reset URLs
    path('password/reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password/reset/email-sent/', PasswordResetEmailSentView.as_view(), name='password-reset-email-sent'),
    path('password/reset/confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]
