import datetime, bcrypt, pytz
from uuid import uuid4
import json
import timeago
from phonenumber_field.modelfields import PhoneNumberField

from django.template.loader import render_to_string

from django.db.models import Max
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _, gettext
from administration.core.loading import get_model
from decimal import Decimal
from django.core.validators import validate_email
import phonenumbers
from administration.core.loading import get_model
from django.shortcuts import reverse
import chargebee
from datetime import date

Profile = get_model("registration", "Profile")

def waiver_directory_path(instance, filename):
    return 'files/waiver/%s/%s' % (str(instance.location_id), filename)

def user_profile_path(instance, filename):
    return f"profile_images/{instance.pk}/{filename}"

def studio_settings_path(instance, filename):
    return f"studio_settings/{instance.pk}/{filename}"

# Create your models here.
class Business(models.Model):
    name = models.CharField(_("Name"),max_length=200)
    customer_type = models.IntegerField(_("Customer Type"),
        default=0
    )  # 0 - no setting, 1 - yoga mat, 2 - bike, 3 - table, 4 - bed, 5 - generic obstruction
    business_id = models.PositiveIntegerField(_("Business ID"),default=1, unique=True)

    NOSHOW_PREPAY_NOTHING = "noshow_prepay_nothing"
    NOSHOW_PREPAY_FLATFEE = "noshow_prepay_flat"
    NOSHOW_PREPAY_PERCENTFEE = "noshow_prepay_percent"
    NOSHOW_PREPAY_FULLREFUND = "noshow_prepay_fullrefund"
    NOSHOW_PREPAY_CHOICES = (
        (NOSHOW_PREPAY_NOTHING, _("Do not automatically refund their payment")),
        (NOSHOW_PREPAY_FLATFEE, _("Automatically refund their payment minus a flat no-show fee")),
        (NOSHOW_PREPAY_PERCENTFEE, _("Automatically refund their payment minus a percentage fee")),
        (NOSHOW_PREPAY_FULLREFUND, _("Automatically refund their payment in full without any no-show fee")),
    )

    NOSHOW_NOTPREPAY_NOTHING = "noshow_notprepay_nothing"
    NOSHOW_NOTPREPAY_FLATFEE = "noshow_notprepay_flat"
    NOSHOW_NOTPREPAY_PERCENTFEE = "noshow_notprepay_percent"
    NOSHOW_NOTPREPAY_FULLCHARGE = "noshow_notprepay_fullcharge"
    NOSHOW_NOTPREPAY_CHOICES = (
        (NOSHOW_NOTPREPAY_NOTHING, _("Do not charge any no-show fee to their account")),
        (NOSHOW_NOTPREPAY_FLATFEE, _("Automatically attempt to charge their payment a flat no-show fee")),
        (NOSHOW_NOTPREPAY_PERCENTFEE, _("Automatically attempt to charge their payment a percentage no-show fee")),
        (NOSHOW_NOTPREPAY_FULLCHARGE, _("Automatically attempt to charge their payment in full as a no-show fee")),
    )

    CURRENCY_DOLLAR = "usd"
    CURRENCY_WON = "krw"

    CURRENCY_TYPE_CHOICES = (
        (CURRENCY_DOLLAR, "$"),
        (CURRENCY_WON, "₩"),
    )

    COUNTRY_CODE_US = "us"
    COUNTRY_CODE_KR = "kr"

    COUNTRY_CODE_CHOICES = (
        (COUNTRY_CODE_US, _("United States")),
        (COUNTRY_CODE_KR, _("South Korea"))
    )  
    default_country_code = models.CharField(_("Default Country Code"),default="us",choices=COUNTRY_CODE_CHOICES, max_length=50, null=True, blank=True)

    EMAIL_PROVIDER_SMTP = "smtp_server"
    EMAIL_PROVIDER_RESEND = "resend"
    EMAIL_PROVIDER_CHOICES = (
        (EMAIL_PROVIDER_SMTP, _("SMTP Server")),
        (EMAIL_PROVIDER_RESEND, _("Resend")),
    )

    late_cancel_hours = models.PositiveIntegerField(_("Number of Hours Ahead After Which Cancellation is Late"),default=0)
    noshow_options_prepay = models.CharField(
        _("When the customer has paid ahead of time and is marked as a no-show during checkin:"),
        max_length=30,
        choices=NOSHOW_PREPAY_CHOICES,
        default=NOSHOW_PREPAY_NOTHING,
    )
    noshow_prepay_flatfee = models.DecimalField(
        _("Flat No-Show Fee when Customer Has Prepaid"),
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    noshow_prepay_percentfee = models.DecimalField(
        _("Percentage No-Show Fee when Customer Has Prepaid"),
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    noshow_options_notprepay = models.CharField(
        _("When the customer has not yet paid and is marked as a no-show during checkin:"),
        max_length=30,
        choices=NOSHOW_NOTPREPAY_CHOICES,
        default=NOSHOW_NOTPREPAY_NOTHING,
    )
    noshow_notprepay_flatfee = models.DecimalField(
        _("Flat No-Show Fee when Customer Hasn't Prepaid"),
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    noshow_notprepay_percentfee = models.DecimalField(
        _("Percentage No-Show Fee when Customer Hasn't Prepaid"),
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    #Embed color settings
    header_color = models.CharField(_("Header Color"),max_length=20, null=True, blank=True)
    button_color = models.CharField(_("Button Color"),max_length=20, null=True, blank=True)
    text_color = models.CharField(_("Text Color"),max_length=20, null=True, blank=True)
    background_color = models.CharField(_("Background Color"),max_length=20, null=True, blank=True)
    button_text_color = models.CharField(_("Button Text Color"),max_length=20, null=True, blank=True)
    secondary_accent_color = models.CharField(_("Secondary Accent Color"),max_length=20, null=True, blank=True)
    highlight_color = models.CharField(_("Highlight Color"),max_length=20, null=True, blank=True)
    font_header = models.CharField(_("Header Font"),max_length=200, null=True, blank=True)
    font_body = models.CharField(_("Body Font"),max_length=200, null=True, blank=True)
    
    #Contact settings
    email_provider = models.CharField(
        _("Email Provider"),
        max_length=20,
        choices=EMAIL_PROVIDER_CHOICES,
        default=EMAIL_PROVIDER_SMTP,
    )
    email_address = models.CharField(_("Send-From Email Address"),max_length=400, null=True, blank=True)
    application_password = models.CharField(_("Application Password"),max_length=400, null=True, blank=True)
    resend_api_key = models.CharField(_("Resend API Key"),max_length=400, null=True, blank=True)
    host_address = models.CharField(_("Host Address"),max_length=400, null=True, blank=True)
    host_port = models.CharField(_("Host Port"),max_length=20, null=True, blank=True)
    host_tls = models.BooleanField(_("Host Using TLS"),default=False)

    contact_email = models.CharField(_("Contact Email Address"),max_length=400, null=True, blank=True)
    contact_phone = models.CharField(_("Contact Phone Number"),max_length=400, null=True, blank=True)
    business_website = models.CharField(_("Business Website"),max_length=400, null=True, blank=True)
    business_address = models.CharField(_("Business Address"), max_length=1000, null=True, blank=True)
    business_registration_number = models.CharField(_("Business Registration Number"), max_length=100, null=True, blank=True)
    business_owner = models.CharField(_("Business Representative"), max_length=100, null=True, blank=True)
    show_contact = models.BooleanField(_("Show Contact Information to Customers"),default=False)
    time_zone_string = models.CharField(_("Time Zone"),max_length=400, null=True, blank=True)
    booking_calendar_enabled = models.BooleanField(_("Booking Calendar Enabled"), default=True)
    booking_event_cards_enabled = models.BooleanField(_("Booking Event Cards Enabled"), default=True)
    event_registration_confirmation_email_enabled = models.BooleanField(_("Send RSVP Confirmation Email"), default=True)
    customer_page_org_name = models.CharField(_("Customer Page Org Name"),max_length=200, null=True, blank=True)
    customer_page_full_name = models.CharField(_("Customer Page Full Name"),max_length=200, null=True, blank=True)
    customer_page_tagline = models.CharField(_("Customer Page Tagline"),max_length=400, null=True, blank=True)

    studio_image = models.ImageField(_("Studio Image"), upload_to=studio_settings_path, blank=True, null=True)

    def __str__(self):
        return self.name

    def default_language(self):
        if self.default_country_code == self.COUNTRY_CODE_US:
            return Profile.LANGUAGE_ENGLISH
        if self.default_country_code == self.COUNTRY_CODE_KR:
            return Profile.LANGUAGE_KOREAN

    def currency(self):
        if self.default_country_code == self.COUNTRY_CODE_US:
            return self.CURRENCY_DOLLAR
        elif self.default_country_code == self.COUNTRY_CODE_KR:
            return self.CURRENCY_WON

    def currency_symbol(self):
        return dict(self.CURRENCY_TYPE_CHOICES).get(self.currency())
    
    def num_staff(self):
        return Profile.objects.filter(user_type=Profile.USER_TYPE_STAFF, business_id=self.business_id, staff_is_active=True).count()

    #These methods return the customized colors if populated - otherwise return the default
    def get_header_color(self):
        if self.header_color:
            return self.header_color
        else:
            return "#EDF1F7"
    def get_button_color(self):
        if self.button_color:
            return self.button_color
        else:
            return "#EC2660"
    def get_text_color(self):
        if self.text_color:
            return self.text_color
        else:
            return "#12263F"
    def get_background_color(self):
        if self.background_color:
            return self.background_color
        else:
            return "#FFFFFF"
    def get_button_text_color(self):
        if self.button_text_color:
            return self.button_text_color
        else:
            return "#FFFFFF"
    def get_secondary_accent_color(self):
        if self.secondary_accent_color:
            return self.secondary_accent_color
        else:
            return "#DD449B"
    def get_highlight_color(self):
        if self.highlight_color:
            return self.highlight_color
        else:
            return "#CFCF5A"
    def get_font_header(self):
        if self.font_header:
            return self.font_header
        else:
            return "'Inter', sans-serif"
    def get_font_body(self):
        if self.font_body:
            return self.font_body
        else:
            return "'Inter', sans-serif"
    def get_customer_page_org_name(self):
        return self.customer_page_org_name or self.name
    def get_customer_page_full_name(self):
        return self.customer_page_full_name or self.name
    def get_customer_page_tagline(self):
        return self.customer_page_tagline or ""

class DomainToBusinessMapping(models.Model):
    domain = models.CharField(_("Domain"),max_length=500)
    business = models.OneToOneField(Business, verbose_name=_("Business"), on_delete=models.CASCADE, related_name="domain_mapping")
    created_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.domain) + " <-> " + str(self.business)

def timezone_choices():
    return [(tz, _(tz)) for tz in pytz.common_timezones]


class Location(models.Model):
    CURRENCY_DOLLAR = "usd"
    CURRENCY_WON = "krw"

    CURRENCY_TYPE_CHOICES = (
        (CURRENCY_DOLLAR, "$"),
        (CURRENCY_WON, "₩"),
    )

    COUNTRY_CODE_US = "us"
    COUNTRY_CODE_KR = "kr"

    COUNTRY_CODE_CHOICES = (
        (COUNTRY_CODE_US, _("United States")),
        (COUNTRY_CODE_KR, _("South Korea"))
    )  

    name = models.CharField(_("Name"),max_length=200)
    country_code = models.CharField(_("Country Code"),default="us",choices=COUNTRY_CODE_CHOICES, max_length=50)
    
    street_address = models.CharField(_("Street Address"),max_length=200, blank=True, null=True)
    city = models.CharField(_("City"),max_length=50, blank=True, null=True)
    state = models.CharField(_("State"),max_length=50, blank=True, null=True)
    ZIPcode = models.CharField(_("ZIP Code"),max_length=20, blank=True, null=True)
    
    time_zone_string = models.CharField(_("Time Zone"),max_length=32, choices=timezone_choices)
    business_hours_from = models.CharField(_("Opening Business Hours"),max_length=10, default='9am')
    business_hours_to = models.CharField(_("Closing Business Hours"),max_length=10, default='8am')
    
    currency = models.CharField(_("Currency"),max_length=50, choices=CURRENCY_TYPE_CHOICES, default='usd')

    business_id = models.PositiveIntegerField(_("Business ID"),default=1)

    #Room object cites this Location object
    def time_zone(self):
        return pytz.timezone(self.time_zone_string)

    def __str__(self):
        return self.name

    @classmethod
    def create_location(cls,input_name):
        new_location = cls(name=input_name)
        new_location.save()
        return new_location

    def full_address_inline(self):
        address = ""
        if self.street_address:
            address += self.street_address + " "
        if self.city:
            address += self.city + " "
        if self.state:
            address += self.state + " "
        if self.ZIPcode:
            address += self.ZIPcode

        return address

class DaysOfOperation(models.Model):
    days = {
        1: _("Monday"),
        2: _("Tuesday"),
        3: _("Wednesday"),
        4: _("Thursday"),
        5: _("Friday"),
        6: _("Saturday"),
        7: _("Sunday")
    }
    day_of_week = models.PositiveIntegerField(_("Day of Week"),default=1)
    is_checked = models.BooleanField(_("enabled"),default=False)
    location = models.ForeignKey(Location, verbose_name=_("Location"), on_delete=models.CASCADE)

    def __str__(self):
        return self.days.get(self.day_of_week)

    @property
    def get_day_name(self):
        return self.days.get(self.day_of_week)

# creating separate to handle multiple uploads against one location
class Waiver(models.Model):
    location = models.ForeignKey(Location, verbose_name=_("Location"), related_name="waivers", on_delete=models.CASCADE)
    waiver_file = models.FileField(_("Waiver File"), upload_to=waiver_directory_path)
    business_id = models.PositiveIntegerField(_("Business ID"), default=1)

class Room(models.Model):
    name = models.CharField(_("Name"), max_length=200)
    location = models.ForeignKey(Location, verbose_name=_("Location"), on_delete=models.CASCADE)
    obstruction = models.BooleanField(_("Obstruction"), default=True)
    length = models.FloatField(_("Length (Feet)"), default=None, null=True, blank=True)       #Units Feet
    width = models.FloatField(_("Width (Feet)"), default=None, null=True, blank=True)       #Units Feet
    business_id = models.PositiveIntegerField(_("Business ID"), default=1)
    
    #Layouts object cites this Room object
    def __str__(self):
        return self.name

    @classmethod
    def create_room(cls,input_name,input_location,input_length,input_width):
        new_room = cls(name=input_name,location=input_location,length=input_length,width=input_width)
        new_room.save()
        return new_room

def default_weekdays():
    """Return a dictionary with weekday names as keys and False values."""
    return {
        'Monday': False,
        'Tuesday': False,
        'Wednesday': False,
        'Thursday': False,
        'Friday': False,
        'Saturday': False,
        'Sunday': False
    }
 
def localized_currency_format(num, business_id):
    business_obj = Business.objects.filter(business_id=business_id).first()
    currency = business_obj.currency()

    if num == "":
        return dict(Business.CURRENCY_TYPE_CHOICES)[currency]
        
    if currency == Business.CURRENCY_WON:
        decimal_places = 0
    elif currency == Business.CURRENCY_DOLLAR:
        decimal_places = 2
    else:
        decimal_places = 2

    rounded_num = round(Decimal(num),decimal_places)
    localized_amount = dict(Business.CURRENCY_TYPE_CHOICES)[currency] + str(rounded_num)

    return localized_amount
