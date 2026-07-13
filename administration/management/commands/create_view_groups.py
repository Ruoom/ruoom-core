import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

from registration.models import Profile
from registration.utils.authentication import get_permission_group_names


logger = logging.getLogger(__file__)


class Command(BaseCommand):
    help = 'Creates groups for the views defined in RESTRICTED_PATH_GROUPS and SUPERUSER_ONLY_PATH_GROUPS defined in settings.'

    def handle(self, *args, **kwargs):
        for group in get_permission_group_names():
            Group.objects.get_or_create(name=group)

        super_users = Profile.objects.filter(is_superuser=True)

        for group in get_permission_group_names(include_default=False):
            user_group, created = Group.objects.get_or_create(name=group)

            for user in super_users:
                user.groups.add(user_group)
        logger.info('Groups successfully created. superusers have been added into "admin" group')
        print('Groups successfully created. superusers have been added into "admin" group')
