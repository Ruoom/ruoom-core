from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.models import User

from registration.models import Profile
from registration.controller import return_business_id_for_domain


class CustomAuthBackend:
    def authenticate(self, request, username=None, password=None):
        if username and password:
            business_id = return_business_id_for_domain(request.META.get('HTTP_HOST', ''))
            profile = Profile.objects.filter(business_id=business_id, username=username)
            user = User.objects.filter(profile__in=profile).first()
            if user:
                if user.check_password(password):
                    return user
        return None

    def get_user(self, user_id):
        user = User.objects.filter(id=user_id).first()
        return user if user else None

