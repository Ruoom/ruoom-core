from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from registration.models import Profile
from registration.controller import return_business_id_for_domain

UserModel = get_user_model()

class DomainPasswordResetForm(PasswordResetForm):
    
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
            **(extra_email_context or {}),
        }

        # Send email
        self.send_mail(
            subject_template_name,
            email_template_name,
            context,
            from_email,
            email,
            html_email_template_name=html_email_template_name,
        )
    