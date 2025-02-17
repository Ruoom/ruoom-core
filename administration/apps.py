import logging

from django.apps import AppConfig
from django.core.management import call_command


logger = logging.getLogger(__file__)


class AdminConfig(AppConfig):
    name = 'administration'
