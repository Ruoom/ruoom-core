from django.urls import reverse

from registration.forms import SigninForm
from ruoom.plugin_metadata import get_plugin_sign_in_options


def signin_context(request):
    """Provide Core's shared sign-in UI with enabled plugin options."""
    signin_url = reverse("registration:signin")
    redirect_url = request.GET.get("next", "")
    if not redirect_url and request.path.rstrip("/") != signin_url.rstrip("/"):
        redirect_url = request.get_full_path()

    return {
        "signin_form": SigninForm(request=request),
        "signin_url": signin_url,
        "redirect_url": redirect_url,
        "plugin_sign_in_options": get_plugin_sign_in_options(),
    }
