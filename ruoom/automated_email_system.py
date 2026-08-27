import logging
import re
from email.utils import formataddr
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


def _contains_html_markup(content):
    if not content:
        return False
    return bool(re.search(r"<[a-z][^>]*>", content, flags=re.IGNORECASE))


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

    button_color = business.get_button_color() if business else "#EC2660"
    text_color = business.get_text_color() if business else "#12263F"
    business_name = business.name if business else ""
    effective_logo_url = _resolve_business_logo_url(business, logo_url=logo_url)

    if effective_logo_url:
        header_html = (
            f'<div id="ruoom-business-header" style="max-width:600px;margin:0 auto;padding:24px 20px;'
            f'border-top:4px solid {button_color};border-bottom:1px solid #E7EAF0;text-align:left;">'
            f'<img src="{effective_logo_url}" alt="{business_name}" '
            f'style="max-height:48px;max-width:180px;display:block;"></div>'
        )
    elif business_name:
        header_html = (
            f'<div id="ruoom-business-header" style="max-width:600px;margin:0 auto;padding:24px 20px;'
            f'border-top:4px solid {button_color};border-bottom:1px solid #E7EAF0;text-align:left;'
            f'color:{text_color};font-family:Arial,sans-serif;font-size:20px;font-weight:700;'
            f'letter-spacing:-0.2px;">{business_name}</div>'
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
    font_header = business.get_font_header() if business else "Arial, sans-serif"
    font_body = business.get_font_body() if business else "Arial, sans-serif"

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

    footer_html = "<span>Sent securely by Ruoom</span>"
    if footer_parts:
        footer_html = "<br>".join(footer_parts)

    logo_url = _resolve_business_logo_url(business)
    if logo_url:
        brand_html = (
            f'<img src="{logo_url}" alt="{business.name}" style="max-height:48px;max-width:180px;'
            f'display:block;border:0;">'
        )
    else:
        brand_html = (
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
            f'<td style="padding-right:10px;"><span style="display:block;width:10px;height:10px;'
            f'border-radius:10px;background-color:{button_color};font-size:0;line-height:0;">&nbsp;</span></td>'
            f'<td style="font-family:{font_header};font-size:20px;line-height:26px;font-weight:700;'
            f'letter-spacing:-0.2px;color:{text_color};">{business.name if business else ""}</td>'
            '</tr></table>'
        )

    return (
        '<!doctype html><html><head><meta charset="UTF-8"><meta name="viewport" '
        'content="width=device-width, initial-scale=1.0">'
        '<style type="text/css">'
        'body{margin:0!important;padding:0!important;width:100%!important;-webkit-text-size-adjust:100%;}'
        'table{border-collapse:collapse;mso-table-lspace:0;mso-table-rspace:0;}'
        'img{border:0;height:auto;line-height:100%;outline:none;text-decoration:none;}'
        f'.email-content{{color:{text_color};font-family:{font_body};font-size:16px;line-height:1.6;}}'
        f'.email-content h1,.email-content h2,.email-content h3{{color:{text_color};font-family:{font_header};'
        'letter-spacing:-0.02em;margin:0 0 14px;}}'
        '.email-content h1{font-size:30px;line-height:1.2}.email-content h2{font-size:21px;line-height:1.3}'
        '.email-content h3{font-size:16px;line-height:1.4}.email-content p{margin:0 0 18px}'
        f'.email-content a{{color:{button_color};}}'
        '.email-eyebrow{font-size:12px;font-weight:700;letter-spacing:.08em;line-height:1.4;margin:0 0 12px;text-transform:uppercase;}'
        '.email-lead{font-size:17px;line-height:1.65}.email-section{margin-top:30px}'
        '.email-panel{background:#F7F8FA;border:1px solid #E7EAF0;border-radius:10px;padding:20px 22px;}'
        '.email-detail-table,.email-summary-table,.email-products{width:100%;}.email-detail-table td,.email-summary-table td{padding:9px 0;vertical-align:top;}'
        f'.email-products td{{color:{text_color};font-size:15px;padding:7px 0;vertical-align:top;}}'
        '.email-products td:last-child{text-align:right}.email-products .email-product-name{text-align:left!important;}'
        '.email-products tr:last-child td{padding-bottom:14px}'
        '.email-detail-table tr+tr td,.email-summary-table tr+tr td{border-top:1px solid #E3E7EC;}'
        '.email-label{color:#667085;font-size:14px;padding-right:18px!important;width:42%;}'
        f'.email-value{{color:{text_color};font-weight:600;text-align:right;}}'
        '.email-detail-table .email-value{padding-left:24px!important;text-align:left;word-break:break-word;}'
        '.email-summary-table .email-value{padding-left:24px!important;white-space:nowrap;}'
        '.email-total td{border-top:2px solid #CDD3DC!important;font-size:17px;padding-top:14px!important;}'
        f'.email-button{{background:{button_color};border-radius:7px;color:{button_text_color}!important;display:inline-block;'
        'font-size:15px;font-weight:700;line-height:20px;padding:13px 20px;text-align:center;text-decoration:none;}}'
        f'.email-button-secondary{{border:1px solid #CDD3DC;border-radius:7px;color:{text_color}!important;display:inline-block;'
        'font-size:15px;font-weight:600;line-height:20px;padding:12px 19px;text-align:center;text-decoration:none;}}'
        '.email-item{border-top:1px solid #E7EAF0;padding:20px 0}.email-item:first-child{border-top:0;padding-top:0}'
        '.email-item:last-child{padding-bottom:0}.email-meta{color:#667085;font-size:14px;line-height:1.55}'
        '.email-note{border-left:3px solid #CDD3DC;color:#667085;font-size:13px;line-height:1.55;padding-left:14px;}'
        '@media only screen and (max-width:640px){.email-shell-pad{padding:12px!important}.email-card{border-radius:12px!important}'
        '.email-masthead{padding:20px 22px!important}.email-content{padding:28px 22px!important}.email-footer{padding:20px 22px!important}'
        '.email-content h1{font-size:26px!important}.email-button,.email-button-secondary{box-sizing:border-box;display:block!important;width:100%!important}}'
        '</style></head>'
        '<body style="margin:0;padding:0;background-color:#F3F5F7;">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        'style="width:100%;background-color:#F3F5F7;"><tr><td class="email-shell-pad" align="center" style="padding:32px 16px;">'
        '<table role="presentation" width="640" cellpadding="0" cellspacing="0" border="0" class="email-card" '
        'style="width:100%;max-width:640px;background-color:#FFFFFF;border:1px solid #E1E5EA;border-radius:16px;overflow:hidden;">'
        f'<tr><td height="5" style="height:5px;background-color:{header_color};font-size:0;line-height:0;">&nbsp;</td></tr>'
        '<tr><td class="email-masthead" style="padding:24px 40px;border-bottom:1px solid #E7EAF0;">'
        f'{brand_html}</td></tr>'
        f'<tr><td class="email-content" style="padding:38px 40px 42px;background-color:{background_color};'
        f'color:{text_color};font-family:{font_body};font-size:16px;line-height:1.6;">{html_content}</td></tr>'
        '<tr><td class="email-footer" style="padding:22px 40px;border-top:1px solid #E7EAF0;background-color:#FAFBFC;'
        f'color:#667085;font-family:{font_body};font-size:12px;line-height:1.6;text-align:center;">{footer_html}</td></tr>'
        '</table></td></tr></table></body></html>'
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
        if from_email and business.name:
            from_email = formataddr((business.name, from_email))
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
        business_name = str(business.name).strip()
        subject_text = str(subject).strip()
        subject_lower = subject_text.casefold()
        business_name_lower = business_name.casefold()
        already_branded = (
            subject_lower == business_name_lower
            or subject_lower.startswith(f"{business_name_lower}:")
            or subject_lower.startswith(f"{business_name_lower} ")
        )
        if not already_branded:
            subject_text = f"{business_name}: {subject_text}"
        subject = subject_text

    if html_content and _is_full_html_document(html_content):
        wrapped_html = _inject_business_header_into_full_html(html_content, business)
    elif html_content:
        wrapped_html = _wrap_email_with_footer(html_content, business)
    elif _is_full_html_document(text_content):
        wrapped_html = _inject_business_header_into_full_html(text_content, business)
    elif _contains_html_markup(text_content):
        wrapped_html = _wrap_email_with_footer(text_content, business)
    else:
        wrapped_html = _wrap_email_with_footer(f'<p style="font-size:16px;">{text_content}</p>', business)

    wrapped_html = _absolutize_html_urls(wrapped_html, business)

    message = EmailMultiAlternatives(subject, text_content, from_email, recipient_email, connection=backend)
    message.attach_alternative(wrapped_html, "text/html")
    for filename, content, mimetype in attachments or []:
        message.attach(filename, content, mimetype)
    message.send()

    return JsonResponse({"message": "success"})
