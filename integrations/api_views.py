"""
API views for receiving vacancies from Dynamics 365 (D365).
"""
import json
import time
from datetime import timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from hmac import compare_digest

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from jobs.models import JobAdvert
from .models import APIKey, APIRequestLog
from system_logs.services import log_exception


FIELD_SPECS = {
    "recruitingId": {"max": 255, "required": True},
    "jobId": {"max": 255, "required": True},
    "jobTitle": {"max": 255, "required": True},
    "jobDescription": {"max": 4000, "required": True},
    "skills": {"max": 4000, "required": False},
    "certificates": {"max": 4000, "required": False},
    "education": {"max": 4000, "required": False},
    "jobTasks": {"max": 4000, "required": False},
    "responsibilities": {"max": 4000, "required": False},
    "yearsOfExperience": {"required": False},
    "location": {"max": 255, "required": False},
    "jobType": {"max": 255, "required": False},
    "jobFunction": {"max": 255, "required": False},
    "endDate": {"required": False},
}

KNOWN_FIELDS = set(FIELD_SPECS.keys())
MISSING = object()

# Maximum length for request/response body logging
MAX_LOG_BODY_LENGTH = 5000


def api_success(message, data=None, status=200):
    payload = {"status": "SUCCESS", "message": message}
    if data is not None:
        payload["data"] = data
    return JsonResponse(payload, status=status)


def api_error(message, error_code="VALIDATION_ERROR", status=400, errors=None, headers=None):
    payload = {"status": "FAILED", "errorCode": error_code, "message": message}
    if errors:
        payload["errors"] = errors
    response = JsonResponse(payload, status=status)
    if headers:
        for key, value in headers.items():
            response[key] = value
    return response


def normalize_string(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join([str(item).strip() for item in value if str(item).strip()])
    return str(value).strip()


def normalize_optional_string(value):
    if value is None:
        return None
    if isinstance(value, list):
        return "; ".join([str(item).strip() for item in value if str(item).strip()])
    return str(value).strip()


def validate_payload(payload, required_fields):
    errors = []
    cleaned = {}

    if not isinstance(payload, dict):
        return None, [{"field": "payload", "message": "JSON object is required"}]

    for field_name, spec in FIELD_SPECS.items():
        raw_value = payload.get(field_name, MISSING)

        if raw_value is MISSING:
            if field_name in required_fields:
                errors.append({"field": field_name, "message": "Required"})
            continue

        if field_name == "yearsOfExperience":
            if raw_value in (None, ""):
                cleaned[field_name] = None
                continue
            try:
                years = int(raw_value)
            except (TypeError, ValueError):
                errors.append({"field": field_name, "message": "Must be an integer"})
                continue
            if years < 0 or years > 50:
                errors.append({"field": field_name, "message": "Must be between 0 and 50"})
                continue
            cleaned[field_name] = years
            continue

        if field_name == "endDate":
            if raw_value in (None, ""):
                cleaned[field_name] = None
                continue
            parsed = parse_end_date(raw_value)
            if parsed is None:
                errors.append({"field": field_name, "message": "Invalid ISO 8601 datetime format"})
                continue
            cleaned[field_name] = raw_value
            continue

        value = normalize_string(raw_value) if spec.get("required", False) else normalize_optional_string(raw_value)

        max_length = spec.get("max")
        if max_length and len(value) > max_length:
            errors.append({"field": field_name, "message": f"Max length is {max_length}"})
            continue

        cleaned[field_name] = value

    return cleaned, errors


def get_api_key(request):
    return request.headers.get("X-API-Key") or request.META.get("HTTP_X_API_KEY")


def get_api_key_object(api_key_value):
    """Get APIKey object from the database."""
    if not api_key_value:
        return None
    try:
        return APIKey.objects.filter(key=api_key_value, is_active=True).first()
    except Exception:
        return None


def is_valid_api_key(api_key):
    """Check if API key is valid (checks both DB and settings for backward compatibility)."""
    if not api_key:
        return False
    
    # Check database first
    api_key_obj = get_api_key_object(api_key)
    if api_key_obj:
        return True
    
    # Fallback to settings (for backward compatibility)
    keys = getattr(settings, "JOBPORTAL_API_KEYS", [])
    for key in keys:
        if key and compare_digest(api_key, key):
            return True
    return False


def check_rate_limit(api_key):
    limit = getattr(settings, "JOBPORTAL_RATE_LIMIT", 100)
    window = getattr(settings, "JOBPORTAL_RATE_WINDOW_SECONDS", 60)
    if not api_key:
        return True, None
    now = timezone.now()
    window_id = int(now.timestamp() // window)
    cache_key = f"jobportal_rate:{api_key}:{window_id}"
    retry_after = int(window - (now.timestamp() % window))
    try:
        count = cache.get(cache_key)
        if count is None:
            cache.set(cache_key, 1, timeout=window)
            return True, None
        if count >= limit:
            return False, retry_after
        cache.incr(cache_key)
        return True, None
    except Exception:
        # Fail open if cache is unavailable
        return True, None


def parse_end_date(end_date_value):
    if not end_date_value:
        return None
    parsed = parse_datetime(end_date_value)
    if parsed is None and " " in end_date_value:
        parsed = parse_datetime(end_date_value.replace(" ", "T"))
    if parsed is None:
        return None
    if timezone.is_naive(parsed):
        try:
            local_tz = ZoneInfo(getattr(settings, "JOBPORTAL_DEFAULT_TIMEZONE", "Africa/Harare"))
        except ZoneInfoNotFoundError:
            local_tz = timezone.get_current_timezone()
        parsed = parsed.replace(tzinfo=local_tz)
    return parsed.astimezone(dt_timezone.utc)


def resolve_end_date(end_date_str):
    parsed = parse_end_date(end_date_str) if end_date_str else None
    if parsed:
        return parsed
    default_days = getattr(settings, "JOBPORTAL_DEFAULT_DEADLINE_DAYS", 30)
    return timezone.now() + timedelta(days=default_days)


def resolve_status(job_advert, deadline):
    """Resolve job status based on deadline and current status."""
    if deadline is None:
        return "OPEN"
    if deadline <= timezone.now():
        return "CLOSED"
    if job_advert and job_advert.status == "CLOSED":
        return "CLOSED"
    return "OPEN"


def get_client_ip(request):
    """Get client IP address from request."""
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        # Validate IP address format (basic check)
        if ip and ('.' in ip or ':' in ip):
            return ip
        return None
    except Exception:
        return None


def get_safe_headers(request):
    """Get request headers excluding sensitive data."""
    headers = {}
    try:
        # Try request.headers (Django 3.2+)
        if hasattr(request, 'headers'):
            for key, value in request.headers.items():
                # Exclude sensitive headers
                if key.lower() not in ['authorization', 'x-api-key', 'cookie']:
                    headers[key] = value
        else:
            # Fallback to META for older Django versions
            for key, value in request.META.items():
                if key.startswith('HTTP_') and key.lower() not in ['http_authorization', 'http_x_api_key', 'http_cookie']:
                    # Convert HTTP_HEADER_NAME to Header-Name
                    header_name = key[5:].replace('_', '-').title()
                    headers[header_name] = value
    except Exception:
        pass
    return headers


def _extract_metadata(request_body):
    """Extract metadata from request body."""
    metadata = {}
    try:
        if request_body and request_body.strip().startswith('{'):
            metadata['recruiting_id'] = json.loads(request_body).get('recruitingId')
    except Exception:
        pass
    return metadata


def log_api_request(request, api_key_obj, response, response_time_ms, error_message=None):
    """Log API request to database."""
    try:
        # Determine response status
        status_code = response.status_code
        if status_code == 200 or status_code == 201:
            response_status = 'SUCCESS'
        elif status_code == 400:
            response_status = 'VALIDATION_ERROR'
        elif status_code == 401:
            response_status = 'UNAUTHORIZED'
        elif status_code == 404:
            response_status = 'NOT_FOUND'
        elif status_code == 409:
            response_status = 'ERROR'
        elif status_code == 429:
            response_status = 'RATE_LIMITED'
        elif status_code >= 500:
            response_status = 'SERVER_ERROR'
        else:
            response_status = 'ERROR'
        
        # Get request body (truncate if too long)
        request_body = ""
        if hasattr(request, 'body') and request.body:
            try:
                body_str = request.body.decode('utf-8')
                request_body = body_str[:MAX_LOG_BODY_LENGTH]
            except Exception:
                pass
        
        # Get response body (truncate if too long)
        response_body = ""
        try:
            # JsonResponse stores content in _container (list of bytes)
            if hasattr(response, '_container') and response._container:
                response_body = b''.join(response._container).decode('utf-8', errors='ignore')[:MAX_LOG_BODY_LENGTH]
            elif hasattr(response, 'content'):
                if isinstance(response.content, bytes):
                    response_body = response.content.decode('utf-8', errors='ignore')[:MAX_LOG_BODY_LENGTH]
                else:
                    response_body = str(response.content)[:MAX_LOG_BODY_LENGTH]
        except Exception:
            pass
        
        # Create log entry
        APIRequestLog.objects.create(
            api_key=api_key_obj,
            method=request.method,
            endpoint=request.path,
            request_body=request_body,
            request_headers=get_safe_headers(request),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            status_code=status_code,
            response_status=response_status,
            response_body=response_body,
            error_message=error_message[:MAX_LOG_BODY_LENGTH] if error_message else '',
            response_time_ms=response_time_ms,
            metadata=_extract_metadata(request_body)
        )
        
        # Update API key last_used_at
        if api_key_obj:
            api_key_obj.mark_used()
    except Exception as e:
        # Don't fail the request if logging fails
        log_exception(
            e,
            source="API",
            module="integrations.api_views",
            function="log_api_request",
            metadata={"error": str(e)}
        )


@csrf_exempt
@require_http_methods(["POST", "PUT"])
def vacancies_endpoint(request):
    start_time = time.time()
    api_key_value = get_api_key(request)
    api_key_obj = get_api_key_object(api_key_value)
    response = None
    error_message = None
    
    try:
        # Validate API key
        if not is_valid_api_key(api_key_value):
            response = api_error("Invalid API key", error_code="UNAUTHORIZED", status=401)
            response_time_ms = int((time.time() - start_time) * 1000)
            log_api_request(request, api_key_obj, response, response_time_ms, "Invalid API key")
            return response

        # Check rate limit
        allowed, retry_after = check_rate_limit(api_key_value)
        if not allowed:
            response = api_error(
                "Rate limit exceeded",
                error_code="RATE_LIMITED",
                status=429,
                headers={"Retry-After": str(retry_after)}
            )
            response_time_ms = int((time.time() - start_time) * 1000)
            log_api_request(request, api_key_obj, response, response_time_ms, "Rate limit exceeded")
            return response

        # Parse request body
        try:
            raw_body = request.body.decode("utf-8") if request.body else "{}"
        except UnicodeDecodeError:
            response = api_error("Invalid UTF-8 payload", error_code="INVALID_ENCODING", status=400)
            response_time_ms = int((time.time() - start_time) * 1000)
            log_api_request(request, api_key_obj, response, response_time_ms, "Invalid UTF-8 payload")
            return response

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            response = api_error("Invalid JSON payload", error_code="INVALID_JSON", status=400)
            response_time_ms = int((time.time() - start_time) * 1000)
            log_api_request(request, api_key_obj, response, response_time_ms, "Invalid JSON payload")
            return response

        # Validate payload
        required_fields = ["recruitingId", "jobId", "jobTitle", "jobDescription"]
        if request.method == "PUT":
            required_fields = ["recruitingId"]

        cleaned, errors = validate_payload(payload, required_fields)
        if errors:
            response = api_error("Validation failed", errors=errors)
            response_time_ms = int((time.time() - start_time) * 1000)
            log_api_request(request, api_key_obj, response, response_time_ms, f"Validation errors: {errors}")
            return response

        # Process request
        try:
            if request.method == "POST":
                existing = JobAdvert.objects.filter(recruiting_id=cleaned["recruitingId"]).first()
                if existing:
                    response = api_error(
                        "Recruiting ID already exists",
                        error_code="DUPLICATE_RECRUITING_ID",
                        status=409
                    )
                    response_time_ms = int((time.time() - start_time) * 1000)
                    log_api_request(request, api_key_obj, response, response_time_ms, "Duplicate recruiting ID")
                    return response
                job_advert = create_vacancy(cleaned)
                response = api_success(
                    "Vacancy successfully published",
                    data={"recruitingId": job_advert.recruiting_id},
                    status=201
                )
            else:  # PUT
                job_advert = JobAdvert.objects.filter(recruiting_id=cleaned["recruitingId"]).first()
                if not job_advert:
                    response = api_error(
                        "Vacancy not found",
                        error_code="NOT_FOUND",
                        status=404
                    )
                    response_time_ms = int((time.time() - start_time) * 1000)
                    log_api_request(request, api_key_obj, response, response_time_ms, "Vacancy not found")
                    return response
                job_advert = update_vacancy(job_advert, cleaned)
                response = api_success(
                    "Vacancy successfully updated",
                    data={"recruitingId": job_advert.recruiting_id},
                    status=200
                )
        except Exception as exc:
            error_message = str(exc)
            log_exception(
                exc,
                source="API",
                module="integrations.api_views",
                function="vacancies_endpoint",
                metadata={"recruiting_id": cleaned.get("recruitingId")}
            )
            response = api_error(
                "Unexpected server error",
                error_code="SERVER_ERROR",
                status=500
            )
        
        # Log successful request
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(request, api_key_obj, response, response_time_ms, error_message)
        return response
        
    except Exception as exc:
        # Catch-all for any unexpected errors
        error_message = str(exc)
        log_exception(
            exc,
            source="API",
            module="integrations.api_views",
            function="vacancies_endpoint",
            metadata={"error": error_message}
        )
        response = api_error(
            "Unexpected server error",
            error_code="SERVER_ERROR",
            status=500
        )
        response_time_ms = int((time.time() - start_time) * 1000)
        log_api_request(request, api_key_obj, response, response_time_ms, error_message)
        return response


def create_vacancy(cleaned):
    with transaction.atomic():
        end_date = resolve_end_date(cleaned.get("endDate"))
        status = resolve_status(None, end_date)

        job_advert = JobAdvert.objects.create(
            recruiting_id=cleaned.get("recruitingId", ""),
            job_id=cleaned.get("jobId", ""),
            job_title=cleaned.get("jobTitle", ""),
            job_description=cleaned.get("jobDescription", ""),
            skills=cleaned.get("skills", ""),
            certificates=cleaned.get("certificates", ""),
            education=cleaned.get("education", ""),
            job_tasks=cleaned.get("jobTasks", ""),
            responsibilities=cleaned.get("responsibilities", ""),
            years_of_experience=cleaned.get("yearsOfExperience"),
            location=cleaned.get("location", ""),
            job_type=cleaned.get("jobType", ""),
            job_function=cleaned.get("jobFunction", ""),
            end_date=end_date,
            status=status
        )
        return job_advert


def update_vacancy(job_advert, cleaned):
    with transaction.atomic():
        for field_name in KNOWN_FIELDS:
            if field_name not in cleaned:
                continue
            if field_name == "recruitingId":
                continue
            if field_name == "yearsOfExperience":
                job_advert.years_of_experience = cleaned.get("yearsOfExperience")
                continue
            if field_name == "endDate":
                end_date_value = cleaned.get("endDate")
                if end_date_value:
                    job_advert.end_date = resolve_end_date(end_date_value)
                    job_advert.status = resolve_status(job_advert, job_advert.end_date)
                continue
            value = cleaned.get(field_name, "")
            attr = field_name
            if field_name == "jobId":
                attr = "job_id"
            elif field_name == "jobTitle":
                attr = "job_title"
            elif field_name == "jobDescription":
                attr = "job_description"
            elif field_name == "jobTasks":
                attr = "job_tasks"
            elif field_name == "jobType":
                attr = "job_type"
            elif field_name == "jobFunction":
                attr = "job_function"
            setattr(job_advert, attr, value)

        job_advert.save()
        return job_advert
