"""
Upload validation middleware.
Enforces a maximum size per uploaded file.
"""
from django.conf import settings
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


class UploadSizeLimitMiddleware(MiddlewareMixin):
    """Reject requests containing files larger than MAX_UPLOAD_FILE_SIZE_BYTES."""

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.FILES:
            return None

        max_bytes = getattr(settings, "MAX_UPLOAD_FILE_SIZE_BYTES", 10 * 1024 * 1024)
        max_mb = max_bytes / (1024 * 1024)

        for uploaded_file in request.FILES.values():
            if uploaded_file.size > max_bytes:
                message = (
                    f"Upload rejected: '{uploaded_file.name}' is {uploaded_file.size / (1024 * 1024):.2f}MB. "
                    f"Maximum allowed size is {max_mb:.0f}MB per file."
                )
                if request.path.startswith("/api/"):
                    return JsonResponse({"error": message}, status=413)
                return HttpResponse(message, status=413)

        return None
