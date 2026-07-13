from django.conf import settings


def is_staff_page_enabled():
    return getattr(settings, "ENABLE_STAFF_PAGE", True)
