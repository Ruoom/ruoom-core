from datetime import timedelta
from django.shortcuts import redirect, resolve_url
from django.urls import reverse, resolve
from django.conf import settings
from django.http import Http404
from django.http import HttpResponseNotFound
from django.utils import timezone
from registration.models import Profile
from administration.helpers import is_ajax
from registration.utils.authentication import can_access
from registration.controller import return_business_id_for_domain
from django.contrib.auth import login

class AuthenticationMiddleware(object):
    """ Authentication middleware to handle following tasks
        - Redirect to superuser creation page if no user exists currently
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check forward none existing domain
        from administration.models import DomainToBusinessMapping
        request_domain = request.META.get('HTTP_HOST', '')
        domain_object = DomainToBusinessMapping.objects.filter(
            domain__icontains=request_domain.lower()
        ).first()

        if not domain_object and "localhost" not in request_domain:
            local_domain = False
            for url in settings.LOCAL_URLS:
                if request_domain in url or url in request_domain:
                    local_domain = True
                    break
            if not local_domain:
                return HttpResponseNotFound("Domain not registered.")

        ### Exempt for all ajax request
        if is_ajax(request):      
            return self.process_request(request)

        #Assign business_id if it is not already assigned
        if hasattr(request.user,"profile"):
            business_id = return_business_id_for_domain(request.META.get('HTTP_HOST', ''))
            if not request.user.profile.business_id and not Profile.objects.filter(business_id=business_id).exists():
                request.user.profile.business_id = business_id
                request.user.profile.save()

        # Force superuser creation if there are none
        if (settings.FORCE_SUPERUSER_CREATION and
                Profile.get_count(is_superuser=True) == 0):
                if request.path != settings.SIGNUP_URL:
                    return redirect(settings.SIGNUP_URL)
                else:
                    return self.process_request(request)

        # Exempt per page permission urls
        elif settings.ENABLE_PER_PAGE_PERMISSIONS:
            allowed_pages = [
                settings.ADMIN_URL1,
                settings.ADMIN_URL2,
                settings.LOGIN_URL,
                settings.SIGNUP_URL,
                settings.CUSTOMER_LOGIN_URL
            ]

            if "customer/appointment" in request.path: #Appointment pages are permitted
                allowed_pages.append(request.path)
            elif "customer/checkout/digitalgood" in request.path: #Permit customer digital good guest checkout, which will have arguments in the path
                allowed_pages.append(request.path)
            elif "customer/payment" in request.path:
                if request.POST.get('guest_cart_id', None) or (request.path.split("=")[-1]).isdigit(): #Posts with guest information can go through
                    allowed_pages.append(request.path)
            elif "admin/subscriptions" in request.path:
                if not request.user.is_staff:
                    raise Http404

            if not request.user.is_authenticated and request.path not in allowed_pages and 'accounts/' not in request.path:
                return redirect(settings.LOGIN_URL)
            elif request.user.is_authenticated and not request.user.is_superuser:
                view = resolve(request.path)
                url_view_name = view.url_name
                if url_view_name in settings.SUPERUSER_ONLY_PATH_GROUPS:
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
