from datetime import datetime
from django import template
import pytz

from administration.core.loading import get_model
from django.utils.translation import gettext_lazy as _
register = template.Library()

Location = get_model('administration', 'Location')

def format_to_24hr(twelve_hour_time):
    return datetime.strftime(
        datetime.strptime(
            twelve_hour_time, '%I:%M %p'
        ), "%H:%M")

@register.filter('get_english_date')
def get_english_date(day, day_date_dict_english):
    return day_date_dict_english[day]

@register.filter('dict_first_val')
def dict_first_val(dict):
    return list(dict.values())[0]

@register.filter('dict_last_val')
def dict_first_val(dict):
    return list(dict.values())[-1]
