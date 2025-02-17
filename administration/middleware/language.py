from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from administration.models import StudioSettings
from ruoom.settings import COUNTRY_LANGUAGES
from registration.controller import return_business_id_for_domain
from django.conf import settings

class LocaleMiddleware(MiddlewareMixin):
    """
    This middleware parses a request
    and decides what translation object to install in the current
    thread context. This allows pages to be dynamically
    translated to the language the user has in profile.
    """

    def process_request(self, request):
      if settings.ADMIN_URL1 in request.path or "webhook" in request.path:
        request.LANGUAGE_CODE = "en"
        return
      if request.user.is_authenticated and request.user.profile.language:
          translation.activate(request.user.profile.language)
          request.LANGUAGE_CODE = translation.get_language()
      else:
          business_id = return_business_id_for_domain(request.META.get('HTTP_HOST', ''))
          obj = StudioSettings.objects.filter(business_id=business_id).first()
          if obj:
            language = COUNTRY_LANGUAGES.get(obj.default_country_code, "en")
          else:
            language = "en"
          translation.activate(language)
          request.LANGUAGE_CODE = translation.get_language()