from django.conf import settings
from django.utils.translation import gettext

from administration.models import Business, DaysOfOperation, Location


def is_location_management_enabled():
    return getattr(settings, "ENABLE_LOCATION_MANAGEMENT", True)


def get_default_location_for_business(business_id, create_if_missing=True):
    location = Location.objects.filter(business_id=business_id).order_by("id").first()
    if location or not create_if_missing:
        return location

    business = Business.objects.filter(business_id=business_id).first()
    country_code = business.default_country_code if business and business.default_country_code else Location.COUNTRY_CODE_US
    time_zone_string = business.time_zone_string if business and business.time_zone_string else "UTC"
    currency = business.currency() if business else Location.CURRENCY_DOLLAR
    location = Location.objects.create(
        name=gettext("Default Location"),
        country_code=country_code,
        time_zone_string=time_zone_string,
        currency=currency,
        business_id=business_id,
    )
    DaysOfOperation.objects.bulk_create(
        [
            DaysOfOperation(day_of_week=day, is_checked=True, location=location)
            for day in DaysOfOperation.days
        ]
    )
    return location
