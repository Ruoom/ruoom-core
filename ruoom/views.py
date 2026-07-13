import base64
import logging
import os
import re
from datetime import datetime, timezone
from io import BytesIO

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
from PIL import Image, UnidentifiedImageError
from django.http import (
    HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest, JsonResponse
)
from django.shortcuts import render
from django.core.files.uploadedfile import InMemoryUploadedFile
from administration.models import Business
from django.views.generic import View
from django.contrib.auth.views import PasswordResetView
from django.shortcuts import render, redirect
from registration.models import Profile
from registration.controller import return_business_id_for_domain

logger = logging.getLogger(__name__)


def health_check(request):
    return JsonResponse({"status": "ok"})


def _get_cgroup_memory():
    memory_current = "/sys/fs/cgroup/memory.current"
    memory_max = "/sys/fs/cgroup/memory.max"
    memory_current_v1 = "/sys/fs/cgroup/memory/memory.usage_in_bytes"
    memory_max_v1 = "/sys/fs/cgroup/memory/memory.limit_in_bytes"
    used_bytes = None
    limit_bytes = None

    try:
        if os.path.exists(memory_current) and os.path.exists(memory_max):
            with open(memory_current, "r", encoding="utf-8") as current_file:
                used_bytes = int(current_file.read().strip())
            with open(memory_max, "r", encoding="utf-8") as max_file:
                max_value = max_file.read().strip()
                if max_value != "max":
                    limit_bytes = int(max_value)
        elif os.path.exists(memory_current_v1) and os.path.exists(memory_max_v1):
            with open(memory_current_v1, "r", encoding="utf-8") as current_file:
                used_bytes = int(current_file.read().strip())
            with open(memory_max_v1, "r", encoding="utf-8") as max_file:
                limit_bytes = int(max_file.read().strip())

        if limit_bytes is None:
            memory_limit = os.environ.get("MEMORY_LIMIT")
            if memory_limit:
                limit_bytes = int(memory_limit)

        if used_bytes is None or limit_bytes is None:
            return None
        if limit_bytes >= 9223372036854771712:
            return None

        return {
            "total_bytes": limit_bytes,
            "used_bytes": used_bytes,
            "percent": round((used_bytes / limit_bytes) * 100, 2),
            "total_mb": round(limit_bytes / (1024 * 1024), 2),
            "used_mb": round(used_bytes / (1024 * 1024), 2),
            "source": "cgroup",
        }
    except (FileNotFoundError, ValueError, ZeroDivisionError, OSError):
        return None


def _get_cgroup_cpu_limit():
    cpu_max = "/sys/fs/cgroup/cpu.max"
    cpu_quota_v1 = "/sys/fs/cgroup/cpu/cpu.cfs_quota_us"
    cpu_period_v1 = "/sys/fs/cgroup/cpu/cpu.cfs_period_us"
    quota = None
    period = None

    try:
        if os.path.exists(cpu_max):
            with open(cpu_max, "r", encoding="utf-8") as cpu_file:
                content = cpu_file.read().strip()
            if content != "max":
                parts = content.split()
                quota = int(parts[0])
                period = int(parts[1]) if len(parts) > 1 else 100000
        elif os.path.exists(cpu_quota_v1) and os.path.exists(cpu_period_v1):
            with open(cpu_quota_v1, "r", encoding="utf-8") as quota_file:
                quota = int(quota_file.read().strip())
            with open(cpu_period_v1, "r", encoding="utf-8") as period_file:
                period = int(period_file.read().strip())
        if quota is not None and period is not None and quota > 0 and period > 0:
            return round(quota / period, 2)
    except (FileNotFoundError, ValueError, OSError):
        return None
    return None


def _get_cgroup_cpu_usage():
    cpu_stat = "/sys/fs/cgroup/cpu.stat"
    cpuacct_usage_v1 = "/sys/fs/cgroup/cpuacct/cpuacct.usage"

    try:
        if os.path.exists(cpu_stat):
            with open(cpu_stat, "r", encoding="utf-8") as stat_file:
                for line in stat_file:
                    if line.startswith("usage_usec"):
                        return int(line.split()[1]) / 1_000_000
    except (FileNotFoundError, ValueError, OSError):
        return None

    try:
        if os.path.exists(cpuacct_usage_v1):
            with open(cpuacct_usage_v1, "r", encoding="utf-8") as usage_file:
                return int(usage_file.read().strip()) / 1_000_000_000
    except (FileNotFoundError, ValueError, OSError):
        return None

    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            return process.cpu_times().user + process.cpu_times().system
        except Exception:
            logger.exception("Unable to read process CPU usage.")
    return None


def api_metrics(request):
    """Token-protected deployment/resource metrics endpoint."""
    from django.conf import settings
    from django.db import connection

    expected_token = getattr(settings, "METRICS_API_TOKEN", None)
    if not expected_token:
        return JsonResponse({"error": "Metrics endpoint not configured"}, status=503)

    provided_token = request.headers.get("X-API-Token", "")
    if not provided_token or provided_token != expected_token:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    data = {
        "status": "OK",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if PSUTIL_AVAILABLE:
        cgroup_vcpu = _get_cgroup_cpu_limit()
        cumulative_seconds = _get_cgroup_cpu_usage()
        data["cpu"] = {
            "count": cgroup_vcpu if cgroup_vcpu is not None else psutil.cpu_count(),
            "cumulative_seconds": cumulative_seconds,
            "source": "cgroup" if cgroup_vcpu is not None else "psutil-host",
        }

        cgroup_memory = _get_cgroup_memory()
        if cgroup_memory:
            data["memory"] = cgroup_memory
        else:
            memory = psutil.virtual_memory()
            data["memory"] = {
                "total_bytes": memory.total,
                "used_bytes": memory.used,
                "percent": memory.percent,
                "total_mb": round(memory.total / (1024 * 1024), 2),
                "used_mb": round(memory.used / (1024 * 1024), 2),
                "source": "psutil-host",
            }

        disk = psutil.disk_usage("/")
        data["disk"] = {
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "percent": round((disk.used / disk.total) * 100, 2),
            "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
            "used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
        }

        process = psutil.Process()
        data["process"] = {
            "memory_mb": round(process.memory_info().rss / (1024 * 1024), 2),
            "cpu_percent": process.cpu_percent(interval=None),
        }
    else:
        data["resources"] = "psutil not available"

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        data["database"] = {"status": "connected"}
    except Exception as exc:
        data["database"] = {"status": "error", "error": str(exc)}

    railway_vars = {
        "deployment_id": os.environ.get("RAILWAY_DEPLOYMENT_ID"),
        "replica_id": os.environ.get("RAILWAY_REPLICA_ID"),
    }
    data["railway"] = {key: value for key, value in railway_vars.items() if value is not None}

    return JsonResponse(data)


def success(request):
    return HttpResponse("Successful Operation.")

def unsuccess(request):
    return HttpResponse("Unsuccessful Operation.")

def handler400(request, exception, template_name="error.html"):
    print(f"Rendering template: {template_name}")
    response = render(request, template_name)
    response.status_code = 400
    return response

def handler403(request, exception, template_name="error.html"):
    print(f"Rendering template: {template_name}")
    return render(request, template_name, status=403)

def handler404(request, exception, template_name="error.html"):
    print(f"Rendering template: {template_name}")
    response = render(request, template_name)
    response.status_code = 404
    return response

def handler500(request, template_name="error.html", *args, **argv):
    print(f"Rendering template: {template_name}")
    return render(request, template_name, status=500)

class SavePictureView(View):
    """Save different kind of image."""

    image_field_name = "image_field_name"
    image_upload_name = "image_upload_name"

    def get_instance(self, request):
        pass

    def _parse_image_upload(self, encoded_file, instance_pk):
        if not encoded_file:
            raise ValueError("No file payload provided.")

        data_url_pattern = re.compile(
            r"^data:(image/(?:jpeg|png));base64,(?P<data>.+)$",
            re.IGNORECASE,
        )
        match = data_url_pattern.match(encoded_file)
        if not match:
            raise ValueError("Unsupported image payload.")

        content_type = match.group(1).lower()
        extension = "png" if content_type == "image/png" else "jpg"
        decoded_file = base64.b64decode(match.group("data"), validate=True)
        image_bytes = BytesIO(decoded_file)
        try:
            image = Image.open(image_bytes)
            image.verify()
            detected_content_type = Image.MIME.get(image.format)
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise ValueError("Decoded payload is not a valid image.") from exc

        if detected_content_type is None or detected_content_type.lower() != content_type:
            raise ValueError("Image payload content does not match declared MIME type.")

        file = BytesIO(decoded_file)

        return InMemoryUploadedFile(
            file,
            field_name=self.image_field_name,
            name=f"{self.image_field_name}_{instance_pk}.{extension}",
            content_type=content_type,
            size=len(decoded_file),
            charset=None,
        )

    def post(self, request, *args, **kwargs):
        # Load instance
        instance, response = self.get_instance(request)
        if response is not None:
            return response

        # Load base64 file into request files
        try:
            image = self._parse_image_upload(request.POST.get("file"), instance.pk)
        except Exception as err_msg:
            return HttpResponseBadRequest(
                f"Fail upload {self.image_upload_name}, detail: %s" % err_msg
            )

        # Load form with files
        try:
            setattr(instance, self.image_field_name, image)
            instance.save()
        except Exception as err_msg:
            return HttpResponseBadRequest(
                f"Fail upload {self.image_upload_name}, detail: %s" % err_msg
            )

        return HttpResponse("Success.", status=200)


class SaveStudioPictureView(SavePictureView):
    """Save studio image."""

    image_field_name = "studio_image"
    image_upload_name = "studio image"

    def get_instance(self, request):
        # Load profile instance
        profile = getattr(request.user, "profile", None)
        if not profile:
            return None, HttpResponseBadRequest("User profile not found.")

        studio = Business.objects.filter(
            business_id=profile.business_id
        ).first()
        if not studio:
            return None, HttpResponseBadRequest("Studio settings not found.")

        return studio, None


class SaveProfilePictureView(SavePictureView):
    """Save staff image."""

    image_field_name = "profile_image"
    image_upload_name = "profile image"

    def get_instance(self, request):
        # Load profile instance
        profile = getattr(request.user, "profile", None)
        if not profile:
            return None, HttpResponseBadRequest("User profile not found.")

        return profile, None


def save_picture(request, **kwargs):
    """Save different kind of image."""
    # Handle other request than post
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    # Load instance
    #instance = get_instance

    # Load profile instance
    profile = getattr(request.user, "profile", None)
    if not profile:
        return HttpResponseBadRequest("User profile not found.")

    studio = Business.objects.filter(
        business_id=profile.business_id
    ).first()
    if not studio:
        return HttpResponseBadRequest("Studio settings not found.")

    # Load base64 file into request files
    try:
        file = BytesIO(
            base64.b64decode(
                re.sub(
                    "data:image/jpeg;base64", "", 
                    request.POST.get("file")
                )
            )
        )
        image = InMemoryUploadedFile(
            file,
            field_name="studio_image",
            name=f"studio_image_{studio.pk}.jpg",
            content_type="image/jpeg",
            size=len(file.getvalue()),
            charset=None
        )
    except Exception as err_msg:
        return HttpResponseBadRequest(
            "Fail upload studio image, detail: %s" % err_msg
        )

    # Load form with files
    try:
        studio.studio_image = image
        studio.save()
    except Exception as err_msg:
        return HttpResponseBadRequest(
            "Fail upload profile image, detail: %s" % err_msg
        )

    return HttpResponse("Success.", status=200)


class PasswordResetViewRuoom(PasswordResetView):

    def post(self, request, *args, **kwargs):
        """Customize post method."""
        # Load params
        email = request.POST.get('email')
        business_id = return_business_id_for_domain(request.META.get('HTTP_HOST', ''))
        profile = Profile.objects.filter(email=email, business_id=business_id).first()
        biz = Business.objects.filter(business_id=business_id).first()
        if not profile or biz is None:
            print("No matching account for business_id: %s and email: %s" % (business_id, email))
            return redirect('/accounts/password_reset/done/')

        # Assign extra context
        self.extra_email_context = {
            "Customer": profile,
            "business_name":biz.name,
            "business_email":biz.contact_email,
            "business_website":biz.business_website,
            "customer_logo":biz.studio_image
        }

        print("Sending password reset email to %s" % email)
        return super(PasswordResetViewRuoom, self).post(request, *args, **kwargs)
