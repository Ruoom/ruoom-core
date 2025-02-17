from django import template
from django.conf import settings
from django.utils import timezone
import timeago
from registration.utils.authentication import can_access
from decimal import Decimal
import pytz
import datetime
from administration.models import StudioSettings

register = template.Library()
FEET_PER_METER = 3.28084

@register.simple_tag
def display_if_has_access( user, permission_group):
    if can_access(user, permission_group):
        return 'block'
    return 'none'


@register.simple_tag
def disable_if_not_admin(user):
    if can_access(user, 'admin'):
        return ''
    return 'disabled'


@register.filter(name="load_profile_image")
def load_profile_image(profile):
    # Load pre condition
    media_url = getattr(settings, "MEDIA_URL", None)
    storage_class = settings.DEFAULT_FILE_STORAGE

    # Load image url
    try:
        image_url = profile.profile_image.url
    except Exception:
        image_url = None

    # Return no image
    if not image_url:
        return

    # Ignore if pre condition not match
    if not media_url or storage_class != "django.core.files.storage.FileSystemStorage":
        return image_url

    return image_url.replace(media_url, "")

@register.simple_tag
def translated_time_ago(start_time=timezone.now(), end_time=timezone.now(), user_langauge='en'):
    return timeago.format(start_time, end_time, user_langauge)

@register.simple_tag
def divide(num1, num2):
    return (num1 / num2)

@register.simple_tag
def feet_to_meters(feet):
    if not feet:
        return ""
    return round(Decimal(feet / FEET_PER_METER),1)

@register.simple_tag
def two_decimals(num):
    return round(Decimal(num),2)

@register.simple_tag
def set_timezone(time_str, timezone): 

    time_dt = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M').replace(tzinfo=datetime.timezone.utc)
    tz = pytz.timezone(timezone)
    new_time_dt = time_dt.astimezone(tz)
    new_time_dt_minusone = new_time_dt
    new_time_str = new_time_dt_minusone.strftime('%Y-%m-%d %H:%M')

    return new_time_str

@register.simple_tag
def localized_currency_format(num, business_id):
    business_obj = StudioSettings.objects.filter(business_id=business_id).first()
    currency = business_obj.currency()

    if num == "":
        return dict(StudioSettings.CURRENCY_TYPE_CHOICES)[currency]
        
    if currency == StudioSettings.CURRENCY_WON:
        decimal_places = 0
    elif currency == StudioSettings.CURRENCY_DOLLAR:
        decimal_places = 2
    else:
        decimal_places = 2

    rounded_num = round(Decimal(num),decimal_places)
    localized_amount = dict(StudioSettings.CURRENCY_TYPE_CHOICES)[currency] + str(rounded_num)

    return localized_amount

@register.simple_tag
def currency_symbol(business_id):
    business_obj = StudioSettings.objects.filter(business_id=business_id).first()
    currency = business_obj.currency()
    return dict(StudioSettings.CURRENCY_TYPE_CHOICES)[currency]

@register.filter(name="trim")
def trim(string):
    return string.strip()

@register.filter('get_english_date')
def get_english_date(day, day_date_dict_english):
    return day_date_dict_english[day]