from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from administration.models import Business
from registration.models import Profile
from registration.controller import return_business_id_for_domain

UserModel = get_user_model()

class DomainPasswordResetForm(PasswordResetForm):

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """Send password resets through the same branded shell as other mail."""
        subject = loader.render_to_string(subject_template_name, context)
        subject = "".join(subject.splitlines())
        reset_link = context.get("password_link", "")
        body = f"Reset your password using this link: {reset_link}"
        html_email = loader.render_to_string("emails/reset-password.html", context)
        business = Business.objects.filter(
            business_id=context.get("business_id")
        ).first()
        if business:
            from ruoom.automated_email_system import _wrap_email_with_footer

            html_email = _wrap_email_with_footer(html_email, business)

        email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        email_message.attach_alternative(html_email, "text/html")
        email_message.send()

    def save(
        self,
        domain_override=None,
        subject_template_name="registration/password_reset_subject.txt",
        email_template_name="registration/password_reset_email.html",
        use_https=False,
        token_generator=default_token_generator,
        from_email=None,
        request=None,
        html_email_template_name=None,
        extra_email_context=None,
    ):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        # Load correct user to reset email
        email = self.cleaned_data["email"]
        business_id = return_business_id_for_domain(request.META.get('HTTP_HOST', ''))
        profile = Profile.objects.filter(business_id=business_id, email=email)
        user = UserModel.objects.filter(profile__in=profile).first()
        if user is None:
            return

        # Load email fill in tempalte
        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override
        
        # Generate mail context
        context = {
            "email": email,
            "domain": domain,
            "site_name": site_name,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "user": user,
            "token": token_generator.make_token(user),
            "protocol": "https" if use_https else "http",
            "business_id": business_id,
            **(extra_email_context or {}),
        }
        reset_path = reverse(
            "password_reset_confirm",
            kwargs={"uidb64": context["uid"], "token": context["token"]},
        )
        domain_base = str(domain).strip().rstrip("/")
        if "://" not in domain_base:
            domain_base = f"{context['protocol']}://{domain_base}"
        context["password_link"] = f"{domain_base}{reset_path}"

        # Send email
        self.send_mail(
            subject_template_name,
            email_template_name,
            context,
            from_email,
            email,
            html_email_template_name=html_email_template_name,
        )
