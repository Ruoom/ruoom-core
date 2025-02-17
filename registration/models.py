from django.utils.translation import gettext_lazy as _
from administration.core.loading import get_model
from django.contrib.auth import get_user_model
from administration.models import *

User = get_user_model()
DEFAULT_TIMEZONE = 'UTC'

def service_image_path(instance, filename):
    return f"service_images/{instance.pk}/{filename}"

def user_profile_path(instance, filename):
    return f"profile_images/{instance.pk}/{filename}"

class Profile(User):

    LANGUAGE_ENGLISH = "en"
    LANGUAGE_KOREAN = "ko"
    LANGUAGES = {
        LANGUAGE_ENGLISH: "English",
        LANGUAGE_KOREAN: "한국어"
    }

    GENDER_TYPE_MALE = "male"
    GENDER_TYPE_FEMALE = "female"
    GENDER_TYPE_NONBINARY = "nonbinary"
    GENDER_TYPE_NOTLISTED = "not listed"
    GENDER_TYPE_PREFERNO = "prefer not to say"

    USER_TYPE_CUSTOMER = "customer"
    USER_TYPE_STAFF = "staff"

    USER_TYPE_CHOICES = (
        (USER_TYPE_CUSTOMER, _("Customer")),
        (USER_TYPE_STAFF, _("Staff"))
    )

    # Add any more genders here.
    GENDER_TYPE_CHOICES = (
        (GENDER_TYPE_FEMALE, _("Female")),
        (GENDER_TYPE_MALE, _("Male")),
        (GENDER_TYPE_NONBINARY, _("Gender variant/Non-conforming")),
        (GENDER_TYPE_NOTLISTED, _("Not Listed")),
        (GENDER_TYPE_PREFERNO, _("Prefer not to say")),
    )

    LANGUAGE_CHOICES = (
        (LANGUAGE_ENGLISH, _("English")),
        (LANGUAGE_KOREAN, _("Korean")),
    )

    user_type = models.CharField(_("User Type"), max_length=10,
                                 choices=USER_TYPE_CHOICES,
                                 default=USER_TYPE_CUSTOMER)
    staff_is_active = models.BooleanField(_("Staff is Active"), default=True)

    phone = PhoneNumberField(_("Phone Number"), blank=True)
    notes = models.CharField(_("Notes"), max_length=5000, null=True, blank=True)

    gender = models.CharField(_("Gender"), max_length=50,
                              choices=GENDER_TYPE_CHOICES,
                              null=True,
                              blank=True)
    language = models.CharField(_("Language"), max_length=2, default=LANGUAGE_ENGLISH, choices=LANGUAGE_CHOICES)
    date_of_birth = models.DateField(_("Date of Birth"), blank=True, null=True)
    profile_image_url = models.TextField(_("Profile Image URL"), blank=True, null=True)
    profile_image = models.ImageField(_("Profile Image"), upload_to=user_profile_path, default='Wall-E.jpg', blank=True)

    street_address = models.CharField(_("Street Address"), max_length=200, null=True, blank=True)
    city = models.CharField(_("City"), max_length=50, null=True, blank=True)
    state = models.CharField(_("State"), max_length=50, null=True, blank=True)
    country = models.CharField(_("Country"), max_length=50, null=True, blank=True)

    #Service object cites this Staff object
    emgcy_cont_name = models.CharField(verbose_name=_("Emergency Contact Name"), max_length=400, null=True, blank=True)
    emgcy_cont_relation = models.CharField(verbose_name=_("Emergency Contact Relationship"), max_length=400, null=True, blank=True)
    emgcy_cont_num = PhoneNumberField(verbose_name=_("Emergency Contact Number"), blank=True, null=True)

    is_teacher = models.BooleanField(verbose_name=_("Is This User a Service Provider?"),default=False)
    message_consent = models.BooleanField(verbose_name=_("May we communicate with you via mobile messages regarding your registrations?"),default=False)
    balance = models.DecimalField(max_digits=8,decimal_places=2, default=0, verbose_name=_("Account Balance"))

    business_id = models.PositiveIntegerField(_("Business ID"), default=1)
    staff_at_locations = models.ManyToManyField('administration.Locations', verbose_name=_("Staff At Locations"), related_name='staff_at_locations', blank=True)
    msa_signed = models.BooleanField(verbose_name=_("Has this user signed the Master Service Agreement?"),default=False)

    default_location = models.ForeignKey('administration.Locations', verbose_name=_("Default Location"),on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.localized_name()
    
    def first_last(self):
        return self.first_name + ' ' + self.last_name

    def first_last_user(self):
        return self.first_name + ' ' + self.last_name + ' ' + '('+str(self.user_type) + ')'

    def last_first(self):
        return self.last_name + ' ' + self.first_name

    def localized_name(self):
        if self.language == self.LANGUAGE_KOREAN:
            return self.last_first()
        else:
            return self.first_last()

    def localized_initials(self):
        if not self.first_name and not self.last_name:
            return ""
        elif not self.first_name:
            return self.last_name[0]
        elif not self.last_name:
            return self.first_name[0]

        if self.language == self.LANGUAGE_KOREAN:
            if len(self.first_name)==2:
                return self.last_name[0] + self.first_name
            else:
                return self.last_name[0] + self.first_name[0]
        else:
            return self.first_name[0] + self.last_name[0]

    def is_customeruser(self):
        return self.USER_TYPE_CUSTOMER == self.user_type

    def is_staffuser(self):
        return self.USER_TYPE_STAFF == self.user_type

    def get_date_of_birth(self):
        return self.date_of_birth.strftime("%b %d, %Y") if self.date_of_birth else _("Not set")
    
    def address(self):
        return str(self.street_address) + ", " + str(self.city) + ", " + str(self.state) + ", " + str(self.country)

    @classmethod
    def create_staff(cls,input_first,input_last,input_email,input_password, input_teacher, business_id):
        pw_hash = bcrypt.hashpw(str.encode(input_password), bcrypt.gensalt()).decode()
        new_staff = cls(first_name = input_first,last_name = input_last,email = input_email, password = pw_hash, is_teacher = input_teacher, business_id=business_id, user_type=Profile.USER_TYPE_STAFF)
        new_staff.save()
        group = Group.objects.filter(name="Staff")
        if group:
            new_staff.groups.add(group.first())
        new_staff.save()
        return new_staff

    @classmethod
    def create_customer(cls, input_first, input_last, input_email, input_password):
        pw_hash = bcrypt.hashpw(str.encode(
            input_password), bcrypt.gensalt()).decode()
        new_customer = cls(first_name=input_first, last_name=input_last,
                          email=input_email, password=pw_hash, user_type=Profile.USER_TYPE_CUSTOMER)
        new_customer.save()
        group = Group.objects.filter(name="Customer")
        if group:
            new_customer.groups.add(group.first())
        new_customer.save()
        return new_customer

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email+","+str(self.business_id)
        super(Profile, self).save(*args, **kwargs)

    @classmethod
    def get_count(cls, **kwargs):
        return cls.objects.filter(**kwargs).count()

    class Meta:
        verbose_name = _('Profile')

    def location(self):
        Locations = get_model("administration", "Locations")

        if self.default_location:
            return self.default_location
        else:
            return Locations.objects.filter(business_id=self.business_id).first()

    def localized_balance(self):
        if self.location():
            currency = self.location().currency
        else:
            currency = "usd"

        if currency == "krw":
            return int(self.balance)

    def business(self):
        StudioSettings = get_model("administration", "StudioSettings")

        business = StudioSettings.objects.filter(business_id=self.business_id).first()
        return business

