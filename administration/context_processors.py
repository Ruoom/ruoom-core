import os
import requests,json
from administration.models import Business
from django.conf import settings
from django.db.models import Q
from registration.models import Profile
from registration.controller import return_business_id_for_domain

def studio_image(request):
    """Load user profile image to template content as static."""
    # Init default image_url
    context = {
        "studio_setting_image": "img/ruoom_logo.png",
    }

    # Handle image url for authenticated user
    if not request.user.is_authenticated:
        return context

    # Load profile
    profile = getattr(request.user, "profile", None)
    if not profile:
        return context

    if request.user.profile.password == settings.FIRST_TIME_PASS:
        context["first_time"] = True
    else:
        context["first_time"] = False

    # Load studio settings
    studio_settings = Business.objects.filter(
        business_id=profile.business_id
    ).first()
    
    #Check installed plugins based on what's in folder
    plugins = os.listdir(settings.PLUGINS_DIR)
    context["plugins"] = plugins

    if not studio_settings:
        return context

    context["country_code"] = studio_settings.default_country_code

    # Check if profile image available
    if not studio_settings.studio_image:
        return context

    # Load image url
    image_url = studio_settings.studio_image.url
    try:
        image_path = studio_settings.studio_image.path
    except Exception:
        image_path = None
    storage_class = settings.DEFAULT_FILE_STORAGE
    media_url = getattr(settings, "MEDIA_URL", None)
    if (storage_class == "django.core.files.storage.FileSystemStorage" 
        and media_url):
        # Check if image file exist
        if not os.path.exists(image_path):
            return context

        # Replace media prefix
        image_url = image_url.replace(media_url, "")

    # Replace image context
    context["studio_setting_image"] = image_url

    return context

def language_list(request):
    languages = Profile.LANGUAGES
    return { "languages": languages}
    