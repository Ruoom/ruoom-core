from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme


def is_embedded_signin(request):
    return request.headers.get("X-Ruoom-Embedded-Signin") == "1"


def safe_signin_redirect(request, value):
    if value and url_has_allowed_host_and_scheme(
        value, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
    ):
        return value
    return ""


def signin_success(request, redirect_url):
    return JsonResponse({"authenticated": True, "redirect_url": redirect_url})
