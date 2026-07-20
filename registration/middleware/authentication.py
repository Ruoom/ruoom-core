from datetime import timedelta
from django.shortcuts import redirect, resolve_url
from django.urls import reverse, resolve
from django.conf import settings
from django.http import Http404
from django.http import HttpResponseNotFound
from django.utils import timezone
from registration.models import Profile
from registration.utils.authentication import can_access
from registration.controller import return_business_id_for_domain
from administration.domain_bootstrap import normalize_domain
from django.contrib.auth import login
from ruoom.plugin_metadata import (
    get_plugin_public_url_patterns,
    get_plugin_staff_only_url_patterns,
)


def _path_matches_exact(path, candidates):
    normalized_path = path.lstrip("/")
    return any(
        path == str(candidate) or normalized_path == str(candidate).lstrip("/")
        for candidate in candidates
    )


def _path_matches_pattern(path, candidates):
    normalized_path = path.lstrip("/")
    return any(
        path.startswith(str(candidate)) or normalized_path.startswith(str(candidate).lstrip("/"))
        for candidate in candidates
    )


def _is_public_checkout_request(request):
    if not request.path.startswith("/payment/checkout"):
        return False
    return bool(request.GET.get("cart")) or bool(request.POST.get("new_customer_email"))


class AuthenticationMiddleware(object):
    """ Authentication middleware to handle following tasks
        - Redirect to superuser creation page if no user exists currently
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _is_app_staff(self, request):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        profile = getattr(request.user, "profile", None)
        return bool(profile and profile.user_type == Profile.USER_TYPE_STAFF)

    def __call__(self, request):
        # Deployment probes must reach their own lightweight/token checks before
        # domain registration, login, or first-superuser bootstrap enforcement.
        if request.path in ("/health/", "/health", "/api/metrics/"):
            return self.get_response(request)

        # Check forward none existing domain
        from administration.models import DomainToBusinessMapping
        request_domain = normalize_domain(request.META.get('HTTP_HOST', ''))
        domain_object = next(
            (
                mapping
                for mapping in DomainToBusinessMapping.objects.all()
                if normalize_domain(mapping.domain) == request_domain
            ),
            None,
        )

        if not domain_object and not any(
            request_domain == normalize_domain(url) for url in settings.LOCAL_URLS
        ):
            return HttpResponseNotFound("Domain not registered.")

        public_url_patterns = tuple(settings.PUBLIC_URL_PATTERNS) + get_plugin_public_url_patterns()
        staff_only_patterns = tuple(settings.STAFF_ONLY_URL_PATTERNS) + get_plugin_staff_only_url_patterns()

        is_public_path = (
            _path_matches_exact(request.path, settings.PUBLIC_URL_EXACT)
            or _path_matches_pattern(request.path, public_url_patterns)
            or _is_public_checkout_request(request)
        )

        #Assign business_id if it is not already assigned
        if hasattr(request.user,"profile"):
            business_id = return_business_id_for_domain(request.META.get('HTTP_HOST', ''))
            if not request.user.profile.business_id and not Profile.objects.filter(business_id=business_id).exists():
                request.user.profile.business_id = business_id
                request.user.profile.save()

        # Force superuser creation if there are none
        if (settings.FORCE_SUPERUSER_CREATION and
                Profile.get_count(is_superuser=True) == 0):
                if not is_public_path and request.path != str(settings.SIGNUP_URL):
                    return redirect(settings.SIGNUP_URL)
                else:
                    return self.process_request(request)

        # Exempt per page permission urls
        elif settings.ENABLE_PER_PAGE_PERMISSIONS:
            if (
                _path_matches_pattern(request.path, staff_only_patterns)
                and not self._is_app_staff(request)
            ):
                raise Http404

            if not request.user.is_authenticated and not is_public_path:
                return redirect(settings.LOGIN_URL)
            elif request.user.is_authenticated and not request.user.is_superuser:
                view = resolve(request.path)
                url_view_name = view.url_name
                if (
                    url_view_name in settings.SUPERUSER_ONLY_PATH_GROUPS
                    and not can_access(request.user, url_view_name)
                ):
                    raise Http404
                elif url_view_name in settings.RESTRICTED_PATH_GROUPS and not can_access(request.user, url_view_name):
                    raise Http404

        return self.process_request(request)

    def process_request(self, request):
        response = self.get_response(request)
        return response
    
from django.utils.deprecation import MiddlewareMixin
class CookieSameSiteMiddlerTest(MiddlewareMixin):
    """ Authentication middleware to handle following tasks
        - Redirect to superuser creation page if no user exists currently
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.process_request(request)

    def process_request(self, request):
        response = self.get_response(request)
        if 'csrftoken' in response.cookies:
            response.cookies['csrftoken']['samesite'] = 'None'
        if 'sessionid' in response.cookies:
            response.cookies['sessionid']['samesite'] = 'None'
        return response
