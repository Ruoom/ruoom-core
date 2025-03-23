from django import template
from administration.core.loading import get_model
from ruoom.settings import COUNTRY_LANGUAGES

register = template.Library()

Profile = get_model('registration', 'Profile')
Business = get_model('administration', 'Business')

@register.filter('language_verbose')
def language_verbose( language_code):
    if language_code:
        return Profile.LANGUAGES[language_code]
    else:
        return "English"
