import logging
import re
from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

from administration.models import Business
from security.key_lock import RuoomSecurity


logger = logging.getLogger(__name__)


def _business_app_base_url(business):
    if not business:
        return ""

    domain = ""
    try:
        domain = business.domain_mapping.domain or ""
    except (AttributeError, ObjectDoesNotExist):
        pass
    if not domain:
        domain = getattr(business, "business_website", "") or ""
    if not domain:
        return ""

    domain = str(domain).strip().rstrip("/")
    if "://" not in domain:
        hostname = domain.split(":", 1)[0].lower()
        scheme = "http" if hostname in {"localhost", "127.0.0.1", "[::1]"} else "https"
        domain = f"{scheme}://{domain}"
    return domain


def _absolutize_html_urls(html_content, business):
    base_url = _business_app_base_url(business)
    if not html_content or not base_url:
        return html_content

    ignored_schemes = {"cid", "data", "javascript", "mailto", "tel"}

    def replace_url(match):
        value = match.group("url").strip()
        parsed = urlparse(value)
        if (
            not value
            or value.startswith(("#", "//"))
            or parsed.scheme.lower() in ignored_schemes
            or parsed.scheme
        ):
            return match.group(0)
        absolute_url = urljoin(base_url + "/", value)
        return f'{match.group("prefix")}{absolute_url}{match.group("quote")}'

    return re.sub(
        r'(?P<prefix>\b(?:href|src)\s*=\s*(?P<quote>["\']))(?P<url>.*?)(?P=quote)',
        replace_url,
        html_content,
        flags=re.IGNORECASE,
    )


def _is_full_html_document(html_content):
    if not html_content:
        return False
    lower = html_content.lower()
    return "<html" in lower and "<body" in lower


def _resolve_business_logo_url(business, logo_url=None):
    if hasattr(logo_url, "url"):
        logo_url = logo_url.url
    if logo_url and str(logo_url).startswith(("http://", "https://", "data:")):
        return str(logo_url)
    if not logo_url and business and getattr(business, "studio_image", None):
        studio_image = business.studio_image
        logo_url = getattr(studio_image, "url", None) or f"{settings.MEDIA_URL}{studio_image}"
    if not logo_url:
        return None

    logo_url = str(logo_url)
    if logo_url.startswith(("http://", "https://", "data:")):
        return logo_url

    base_url = _business_app_base_url(business)

    if base_url:
        if not logo_url.startswith("/"):
            logo_url = f"/{logo_url}"
        return f"{base_url}{logo_url}"
    return logo_url


def _inject_business_header_into_full_html(html_content, business, logo_url=None):
    if not html_content:
        return html_content
    if 'id="ruoom-business-header"' in html_content or "id='ruoom-business-header'" in html_content:
        return html_content

    header_color = business.get_header_color() if business else "#EDF1F7"
    button_color = business.get_button_color() if business else "#EC2660"
    business_name = business.name if business else ""
    effective_logo_url = _resolve_business_logo_url(business, logo_url=logo_url)

    if effective_logo_url:
        header_html = (
            f'<div id="ruoom-business-header" style="padding:20px;background-color:{header_color};'
            f'text-align:center;border-bottom:1px solid #e3ebf6;"><img src="{effective_logo_url}" '
            f'alt="{business_name}" style="max-height:60px;max-width:220px;display:inline-block;"></div>'
        )
    elif business_name:
        header_html = (
            f'<div id="ruoom-business-header" style="padding:20px;background:linear-gradient(135deg,'
            f'{header_color} 0%,{button_color} 100%);text-align:center;color:#ffffff;'
            f'font-family:Arial,sans-serif;font-size:22px;font-weight:700;">{business_name}</div>'
        )
    else:
        return html_content

    updated_html, count = re.subn(
        r"(<body[^>]*>)",
        r"\1" + header_html,
        html_content,
        count=1,
        flags=re.IGNORECASE,
    )
    if count:
        return updated_html
    return header_html + html_content


def _wrap_email_with_footer(html_content, business):
    header_color = business.get_header_color() if business else "#EDF1F7"
    button_color = business.get_button_color() if business else "#EC2660"
    text_color = business.get_text_color() if business else "#12263F"
    background_color = business.get_background_color() if business else "#FFFFFF"
    button_text_color = business.get_button_text_color() if business else "#FFFFFF"

    footer_parts = []
    if business:
        if business.name:
            footer_parts.append(f"<strong style='color:{text_color};'>{business.name}</strong>")
        contact_line = []
        if business.contact_email:
            contact_line.append(
                f"<a href='mailto:{business.contact_email}' style='color:{button_color};"
                f"text-decoration:none;'>{business.contact_email}</a>"
            )
        if business.contact_phone:
            contact_line.append(f"<span style='color:{text_color};'>{business.contact_phone}</span>")
        if business.business_website:
            contact_line.append(
                f"<a href='{business.business_website}' style='color:{button_color};"
                f"text-decoration:none;'>{business.business_website}</a>"
            )
        if contact_line:
            footer_parts.append(" | ".join(contact_line))
        if business.business_address:
            footer_parts.append(f"<span style='color:{text_color};'>{business.business_address}</span>")

    footer_html = ""
    if footer_parts:
        footer_html = (
            f'<div style="margin-top:40px;padding:20px;border-top:3px solid {button_color};'
            f'font-size:12px;text-align:center;background-color:#f8f9fa;color:{text_color};">'
            f'{"<br>".join(footer_parts)}</div>'
        )

    logo_url = _resolve_business_logo_url(business)
    if logo_url:
        logo_html = (
            f'<div style="background-color:{header_color};padding:20px;border-radius:8px 8px 0 0;'
            f'text-align:center;"><img src="{logo_url}" alt="{business.name}" style="max-height:60px;'
            f'max-width:200px;display:block;margin:0 auto;"></div>'
        )
    else:
        logo_html = (
            f'<div style="padding:20px;background:linear-gradient(135deg,{header_color} 0%,'
            f'{button_color} 100%);border-radius:8px 8px 0 0;text-align:center;">'
            f'<h2 style="margin:0;color:{button_text_color};font-family:Arial,sans-serif;'
            f'font-size:24px;">{business.name if business else ""}</h2></div>'
        )

    return (
        '<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;'
        'background-color:#ffffff;border-radius:8px;box-shadow:0 4px 6px rgba(0,0,0,0.1);">'
        f"{logo_html}"
        f'<div style="padding:30px;color:{text_color};background-color:{background_color};">{html_content}</div>'
        f"{footer_html}</div>"
    )


def _configured_backend_for_business(studio_obj, ruoom_security):
    if not studio_obj or not studio_obj.email_address:
        return None

    if studio_obj.email_provider == Business.EMAIL_PROVIDER_RESEND:
        if not studio_obj.resend_api_key:
            return None
        try:
            from anymail.backends.resend import EmailBackend as ResendEmailBackend
        except ImportError:
            return "missing_resend_backend"
        resend_api_key = ruoom_security.decrypt_message(encrypted_message=studio_obj.resend_api_key)
        return ResendEmailBackend(api_key=resend_api_key, fail_silently=False)

    if studio_obj.host_address and studio_obj.application_password:
        application_password = ruoom_security.decrypt_message(
            encrypted_message=studio_obj.application_password
        )
        return EmailBackend(
            host=studio_obj.host_address,
            port=studio_obj.host_port,
            username=studio_obj.email_address,
            password=application_password,
            use_tls=studio_obj.host_tls,
            fail_silently=False,
        )
    return None


def automated_email_send(
    recipient_email,
    subject,
    text_content,
    business_id=None,
    html_content=None,
    attachments=None,
):
    logger.info("Sending email to %s for %s", recipient_email, subject)

    from_email = ""
    backend = None
    business = Business.objects.filter(business_id=business_id).first() if business_id else None
    if business:
        ruoom_security = RuoomSecurity()
        from_email = business.email_address or ""
        backend = _configured_backend_for_business(business, ruoom_security)
        if backend == "missing_resend_backend":
            return JsonResponse({"message": "Resend backend is not installed"})

    if not backend and settings.EMAIL_HOST:
        backend = EmailBackend(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            fail_silently=False,
        )
        if not from_email:
            from_email = settings.EMAIL_HOST_USER

    if not from_email or not backend:
        return JsonResponse({"message": "No email configured"})

    if business and business.name:
        subject = f"{business.name}: {subject}"

    if html_content and _is_full_html_document(html_content):
        wrapped_html = _inject_business_header_into_full_html(html_content, business)
    elif html_content:
        wrapped_html = _wrap_email_with_footer(html_content, business)
    elif _is_full_html_document(text_content):
        wrapped_html = _inject_business_header_into_full_html(text_content, business)
    else:
        wrapped_html = _wrap_email_with_footer(f'<p style="font-size:16px;">{text_content}</p>', business)

    wrapped_html = _absolutize_html_urls(wrapped_html, business)

    message = EmailMultiAlternatives(subject, text_content, from_email, recipient_email, connection=backend)
    message.attach_alternative(wrapped_html, "text/html")
    for filename, content, mimetype in attachments or []:
        message.attach(filename, content, mimetype)
    message.send()

    return JsonResponse({"message": "success"})
