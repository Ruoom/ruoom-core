from django.http import Http404
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext_lazy as _

from registration.models import Profile
from ruoom.plugin_metadata import get_plugin_permission_groups


def _unique_ordered(items):
    return tuple(dict.fromkeys(items))


def get_permission_group_names(include_default=True, include_superuser_only=True):
    group_names = list(settings.RESTRICTED_PATH_GROUPS)
    if include_superuser_only:
        group_names.extend(settings.SUPERUSER_ONLY_PATH_GROUPS)
    group_names.extend(get_plugin_permission_groups())
    if include_default:
        group_names.extend(settings.DEFAULT_PATH_GROUPS)
    else:
        default_groups = set(settings.DEFAULT_PATH_GROUPS)
        group_names = [group for group in group_names if group not in default_groups]
    return _unique_ordered(group_names)


def get_permission_group_choices():
    return [
        (
            group,
            _("%(permission)s Page") % {
                "permission": group.replace("_", " ").title()
            },
        )
        for group in get_permission_group_names(include_default=False)
    ]


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
    groups = []
    for group_name in _unique_ordered(groups_names_list):
        if not group_name:
            continue
        group, _created = Group.objects.get_or_create(name=group_name)
        groups.append(group)
    user.groups.set(groups)


def can_access(user, permission_group):
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return user.groups.filter(name=permission_group).exists()
