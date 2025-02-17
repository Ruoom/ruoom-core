import os
from posixpath import splitext
import regex


from django import forms
from django.conf import settings
from django.contrib.auth.models import Group

from registration.utils.authentication import authenticate_with_email, set_user_groups

from django.utils.translation import gettext_lazy as _

from administration.models import StudioSettings
from registration.models import Profile
from registration.controller import return_business_id_for_domain
from ruoom.settings import COUNTRY_LANGUAGES

class CreateCustomerForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput(), label=_('Password')
    )

    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'email', 'phone', 'password']

    def __init__(self, *args, **kwargs):
        super(CreateCustomerForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

    def save(self, request, business_id):
        email = self.cleaned_data["email"]
        if Profile.objects.filter(business_id=business_id, email=email):
            self.add_error('email', _("A user with this email already exists"))
            return False

        customer = super(CreateCustomerForm, self).save(request)
        customer.user_type = Profile.USER_TYPE_CUSTOMER
        customer.business_id = request.user.profile.business_id
        group = Group.objects.filter(name="Customer")
        obj = StudioSettings.objects.filter(business_id=customer.business_id).first()
        customer.language = COUNTRY_LANGUAGES.get(obj.default_country_code, "en") 
        if group:
            customer.groups.add(group.first())
        customer.set_password(self.cleaned_data.get('password'))
        customer.save()
        return True

class UpdateCustomerForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ['password', 'notes']

    def __init__(self, *args, **kwargs):
        super(UpdateCustomerForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

class SignupForm(forms.ModelForm):
    #TODO: should use django password validator ?

    password_2 = forms.CharField(
        widget=forms.PasswordInput(), label=_('Verify Password')
    )

    class Meta:
        model = Profile
        fields = ['first_name', 'email', 'password', 'phone','message_consent']

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        self.fields['password'].widget = forms.PasswordInput()
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = '{}'.format(
                visible.field.label)
            if 'Password' in visible.field.label:
                visible.field.widget.attrs['class'] += ' form-control-appended'
                visible.field.widget.attrs['placeholder'] = _("Password")
            if 'Verify Password' in visible.field.label:
                visible.field.widget.attrs['placeholder'] = _('Password Again')
            if 'Phone' in visible.field.label:
                visible.field.widget.attrs['placeholder'] = _("Phone Number (Optional)")
            if 'Email' in visible.field.label:
                visible.field.widget.attrs['placeholder'] = _("Email Address")
            if 'First name' in visible.field.label:
                visible.field.widget.attrs['placeholder'] = _("Name")

    def clean(self):
        super(SignupForm, self).clean()
        password = self.cleaned_data['password']
        password_2 = self.cleaned_data['password_2']
        if password != password_2:
            self.add_error('password_2', _('Passwords do not match'))

    def save(self, business_id):
        email = self.cleaned_data["email"]
        if Profile.objects.filter(business_id=business_id, email=email):
            self.add_error('email', _("A user with this email already exists"))
            return False
        del self.cleaned_data['password_2']
        full_name = self.cleaned_data['first_name'].strip()

        if not StudioSettings.objects.filter(business_id=business_id):
            StudioSettings.objects.create(business_id=business_id)

        language_code = StudioSettings.objects.filter(business_id=business_id).first().default_language()
        first_name, last_name = parse_fullname(full_name, language_code)
        
        user = Profile(**self.cleaned_data)
        user.set_password(self.cleaned_data['password'])
        if not StudioSettings.objects.all().exists():
            StudioSettings.objects.create(business_id=os.environ.get('BUSINESS_ID', 1))
        if Profile.get_count(is_superuser=True) and Profile.get_count(business_id=business_id):
            user.is_superuser = False
            user.user_type = Profile.USER_TYPE_CUSTOMER
            user.save()
        else:
            user.is_superuser = True
            user.first_name = first_name
            user.last_name = last_name
            user.user_type = Profile.USER_TYPE_STAFF
            user.username = email+","+str(business_id)
            # Hard coded business ID for sign up. TBD
            user.save()
            group = Group.objects.filter(name="Profile")
            if group:
                user.groups.add(group.first())
            user.save()
            set_user_groups(user, settings.RESTRICTED_PATH_GROUPS + settings.SUPERUSER_ONLY_PATH_GROUPS)
        return user

class SigninForm(forms.Form):
    email = forms.EmailField(label=_('Email Address'), max_length=100)
    password = forms.CharField(
        label='Password', widget=forms.PasswordInput)  # Encrypted

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(SigninForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = '{}'.format(
                visible.field.label)
            if 'Password' in visible.field.label:
                visible.field.widget.attrs['class'] += ' form-control-appended'
                visible.field.widget.attrs['placeholder'] = _("Password")
            if 'Email Address' in visible.field.label:
                visible.field.widget.attrs['placeholder'] = _("Email Address")

    def clean(self, *args, **kwargs):
        super(SigninForm,self).clean()
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        business_id = return_business_id_for_domain(self.request.META.get('HTTP_HOST', ''))
        user = authenticate_with_email(email=email, password=password, business_id=business_id)
        if user:
            self.user = user
        else:
            self.add_error('password', 'email and password do no match an existing record. Please try again.')

def parse_fullname(full_name, language_code=None):
    if not full_name:
        return "", ""
    full_name_words = full_name.split()

    if language_code == "ko":
        if len(full_name_words) == 1:                       #If the name only has one word
            if regex.search(r'\p{IsHangul}', full_name):        #If the name has Korean Hangul characters, we'll split it up
                if len(full_name) == 3:
                    first_name = full_name[1:3]
                    last_name = full_name[0]
                elif len(full_name) == 4:
                    first_name = full_name[2:4]
                    last_name = full_name[0:2]
                else:                                       #If the name isn't 3 or 4 characters, it probably isn't a full Korean name. First name only.
                    first_name = full_name
                    last_name = ""
            else:                                           #Otherwise, we'll assume it's the first name        
                first_name = full_name
                last_name = ""
        else:
            first_name = full_name_words[1]
            last_name = full_name_words[0]
    else:
        if len(full_name_words) == 1: #If the name only has one word, we'll assume it's the first name
            first_name = full_name
            last_name = ""
        else:
            first_name = full_name_words[0]
            last_name = full_name_words[1]

    return first_name, last_name