"""Middleware for account security flows."""
from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordResetMiddleware:
    """
    Redirect authenticated users to mandatory password reset page
    until their temporary password is changed.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and user.force_password_reset:
            allowed_paths = {
                reverse("first-login-password-reset"),
                reverse("logout"),
            }

            if (
                request.path not in allowed_paths
                and not request.path.startswith("/static/")
                and not request.path.startswith("/media/")
            ):
                return redirect("first-login-password-reset")

        return self.get_response(request)
