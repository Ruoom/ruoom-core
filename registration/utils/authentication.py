from django.http import Http404
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt

from registration.models import Profile


def verify_no_superuser_exists(func):
    """ Decorator to verify that no superuser exists before accessing the superuser signup page """
    def inner(request, *args, **kwargs):
        if Profile.get_count(is_superuser=True):
            raise Http404
        return func(request, *args, **kwargs)
    return inner


def anonymous_required(function, redirect_to=settings.LOGIN_REDIRECT_URL):
    """Decorator for views that checks that the user is NOT logged in, redirecting
    to the homepage if not specified.
    """
    def inner(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(redirect_to)
        return function(request, *args, **kwargs)
    return inner

def authenticate_with_email(email, password, business_id):
    try:
        user = Profile.objects.filter(email=email, business_id=business_id).first()
        if not user:
            return None
    except Profile.DoesNotExist:
        return None
    else:
        if user.check_password(password):
            return user
        return None


def set_user_groups(user, groups_names_list):
    try:
        groups = [ 
            group for gname in groups_names_list 
            for group in Group.objects.filter(
                name__in=[gname, gname.lower()]
            ) 
            
        ]
        user.groups.set(groups)
    except Group.DoesNotExist:
        return None


def can_access(user, permission_group):
    return user.groups.filter(name=permission_group)
