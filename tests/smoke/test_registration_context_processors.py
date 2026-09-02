from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory

from ruoom.plugin_metadata import PluginSignInOption
from registration.context_processors import signin_context


def test_signin_context_exposes_plugin_options_without_redirecting_back_to_signin(
    monkeypatch,
):
    option = PluginSignInOption(
        label="Email me a sign-in code",
        url_name="email_otp:request",
        icon_class="fe fe-mail",
    )
    monkeypatch.setattr(
        "registration.context_processors.get_plugin_sign_in_options",
        lambda: [option],
    )
    request = RequestFactory().get("/registration/signin")

    context = signin_context(request)

    assert context["signin_url"] == "/registration/signin/"
    assert context["redirect_url"] == ""
    assert context["plugin_sign_in_options"] == [option]


def test_signin_context_preserves_an_embedded_page_as_the_post_login_destination():
    request = RequestFactory().get("/digital-store/?currency=KRW")

    context = signin_context(request)

    assert context["redirect_url"] == "/digital-store/?currency=KRW"


def test_plugin_sign_in_options_render_as_links_inside_the_password_form(monkeypatch):
    option = PluginSignInOption(
        label="Email me a sign-in code",
        url_name="email_otp:request",
        icon_class="fe fe-mail",
    )
    monkeypatch.setattr(
        "registration.context_processors.get_plugin_sign_in_options",
        lambda: [option],
    )
    request = RequestFactory().get("/registration/signin/")
    request.user = AnonymousUser()
    context = signin_context(request)

    html = render_to_string(
        "registration/partials/signin_form.html",
        context,
        request=request,
    )

    option_position = html.index("Email me a sign-in code")
    assert html.rfind("<form", 0, option_position) != -1
    assert html.find("</form>", option_position) != -1
    assert 'class="d-inline-block"' in html
    assert "btn-social" not in html
