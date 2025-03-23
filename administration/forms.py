import csv
from datetime import datetime
import io
import os
import re

from django import forms
from django.conf import settings
from administration.models import Business

from registration.utils.authentication import set_user_groups
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from administration.models import Room, Location
from registration.models import Profile
from administration.core.loading import get_model
from django.forms.utils import ErrorList

Profile = get_model("registration","Profile")
Location = get_model("administration", "Location")
Room = get_model("administration", "Room")
Waiver = get_model("administration", "Waiver")

CHOICES = [
    (key, '{} Page'.format(key.title())) for key in settings.RESTRICTED_PATH_GROUPS
    if key not in settings.DEFAULT_PATH_GROUPS
]

class BaseUserForm(forms.ModelForm):
    permissions = forms.MultipleChoiceField(
        choices=CHOICES,
        label='User permissions',
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    locations = forms.ModelChoiceField(
        queryset=Location.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    ) 

    def __init__(self, *args, **kwargs):
        # Load user to process query
        self.user = None
        if "user" in kwargs:
            self.user = kwargs.pop("user")
            
        # Trigger generic init
        super().__init__(*args, **kwargs)
        
        # Super is called twice here to hide password value in form. 
        # Calling super once was not working.
        if "password" in self.Meta.fields:
            # Hide password if instance provide
            if getattr(self, "instance"):
                self.instance.password = ""

            # Trigger other init to hide password                
            super().__init__(*args, **kwargs)

        # Add form control for all fields except user permission
        for visible in self.visible_fields():
            if not visible.field.label == "User permissions":
                visible.field.widget.attrs["class"] = "form-control"

        # Add location relation for location fields
        if self.user:
            self.fields["locations"].queryset = Location.objects.filter(
                business_id=self.user.profile.business_id
            )

    def clean(self):
        # Save permission and locations before clean
        permissions = self.data.getlist("Permissions").copy()
        locations = self.data.getlist("locations").copy()

        # Pop permission and locations
        self.cleaned_data["permissions"] = []
        self.cleaned_data["locations"] = Location.objects.none()

        # Check location
        staff_locations = []
        for location_id in locations:
            # Check exist
            location = Location.objects.filter(
                id=location_id
            ).first()
            if not location:
                self.add_error(
                    "locations", 
                    _(f"Location {location_id} does not exist.")
                )
                continue

            # Check correct business id
            if (self.user 
                and location.business_id != self.user.profile.business_id):
                self.add_error(
                    "locations", 
                    _(
                        f"Location {location_id} does not belong to business {self.user.profile.business_id}."
                    )
                )
                continue

            # Append valid location to list
            staff_locations.append(location)
        
        # Do generic clean
        self.cleaned_data = super().clean()

        # Save permission to clean data
        self.cleaned_data["permissions"] = permissions
        self.cleaned_data["locations"] = staff_locations

        # Remove location error shit
        if self.errors.get("locations"):
            # Init location errors
            location_errors = ErrorList()
            
            # Loop process location erros
            for error in self.errors["locations"]:
                # Ignore error choice not available
                if "not one of the available choices" in str(error):
                    continue
                    
                # Append valid errors
                location_errors.append(error)

            # Assign new location errors
            if len(location_errors) > 0:
                self.errors["locations"] = location_errors
            else:
                del self.errors["locations"]
        
        # Handle User model required procedure
        if "password" in self.Meta.fields:
            password = self.cleaned_data["password"]
            password_2 = self.cleaned_data["password_2"]
            if password != password_2:
                self.add_error("password_2", _("Passwords do not match"))
        else:
            password = "rl9HYY*ou0R4sWh&w3D6E#5*oC#"

        
        # Handle email required
        # email = self.cleaned_data.get('email')
        # if not email:
        #     self.add_error("email", _("email is required!"))

        return self.cleaned_data



    def save(self, *args, **kwargs):
        # Init save user
        staff_user = super().save(*args, **kwargs)
        
        # Handle password
        if "password" in self.Meta.fields:
            staff_user.set_password(self.cleaned_data["password"])
        else:
            password = "rl9HYY*ou0R4sWh&w3D6E#5*oC#"
                    
        # Handle user type
        staff_user.user_type = Profile.USER_TYPE_STAFF

        # Handle staff locations
        staff_user.staff_at_locations.set(self.cleaned_data["locations"])

        # Save update on user
        staff_user.save()

        # Handle permission
        permission_group_names = self.cleaned_data["permissions"]
        if staff_user.is_superuser:
            permission_group_names += settings.SUPERUSER_ONLY_PATH_GROUPS

        # Add default group
        permission_group_names += settings.DEFAULT_PATH_GROUPS

        # Set permission
        set_user_groups(staff_user, permission_group_names)
        
        return staff_user

class CreateUserForm(BaseUserForm):
    """Form to create user."""

    def __init__(self, *args, **kwargs):
        # Init business id if provided
        self.business_id = None
        if "business_id" in kwargs:
            self.business_id = kwargs.get("business_id")
            del kwargs["business_id"]
        super().__init__(*args, **kwargs)
            
    class Meta:
        model = Profile
        fields = [
            'first_name', 'last_name', 'email',
            'is_superuser', 'is_teacher', 'phone', 'permissions','message_consent', 'staff_is_active'
        ]
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    def clean(self):
        super().clean()
        if self.business_id:
            email = self.cleaned_data["email"]
            if Profile.objects.filter(business_id=self.business_id, email=email):
                self.add_error('email', _("A user with this email already exists"))

class UpdateUserForm(BaseUserForm):

    class Meta:
        model = Profile
        fields = [
            'first_name', 'last_name', 'email', 'is_superuser',
            'is_teacher', 'phone', 'permissions','message_consent','staff_is_active'
        ]
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(widget=forms.EmailInput,required=True) 

class CreateStaffForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'email',
                  'phone', 'password', 'is_teacher','staff_is_active']

    def __init__(self, *args, **kwargs):
        super(CreateStaffForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

    def save(self, request):
        staff =  super(CreateStaffForm, self).save(request)
        staff.user_type = Profile.USER_TYPE_STAFF
        staff.business_id = request.user.profile.business_id
        group = Group.objects.filter(name="Staff")
        if group:
            staff.groups.add(group.first())
        staff.save()

class UpdateStaffForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ['password']

    def __init__(self, *args, **kwargs):
        super(UpdateStaffForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

class CreateLocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'street_address', 'city',
                  'state', 'ZIPcode', 'time_zone_string',
                  'business_hours_from', 'business_hours_to',
                  'currency']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control','id':'location_name'}),
            'street_address': forms.TextInput(attrs={'class': 'form-control','id':'location_address'}),
            'city': forms.TextInput(attrs={'class': 'form-control','id':'location_city'}),
            'state': forms.TextInput(attrs={'class': 'form-control','id':'location_state'}),
            'ZIPcode': forms.TextInput(attrs={'class': 'form-control','id':'location_zipcode'}),
            'time_zone_string': forms.Select(attrs={'class': 'form-control','id':'location_time'}),
        }

class CreateRoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'location', 'length', 'width']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'length': forms.NumberInput(attrs={'class': 'form-control'}),
            'width': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, business_id, *args, **kwargs):
        super(CreateRoomForm, self).__init__(*args, **kwargs)
        locations = Location.objects.filter(business_id=business_id)
        self.fields['location'].queryset = locations        

        default_country = Business.objects.get(business_id=business_id).default_country_code

        for visible in self.visible_fields():
            if 'Length' in visible.field.label:
                if default_country == "kr":
                    visible.field.widget.attrs['placeholder'] = _('Meters')
                else:
                    visible.field.widget.attrs['placeholder'] = _('Feet')
            if 'Width' in visible.field.label:
                if default_country == "kr":
                    visible.field.widget.attrs['placeholder'] = _('Meters')
                else:
                    visible.field.widget.attrs['placeholder'] = _('Feet')
            if 'Name' in visible.field.label:
                visible.field.widget.attrs['placeholder'] = _('Name')
          
class UploadWaiverForm(forms.ModelForm):
    class Meta:
        model = Waiver
        fields = []

    def save(self, request):
        location = Location.objects.get(pk=request.POST.get('location_id'))
        file = request.FILES['file']

        # handle file saving here. Verify path of file as well .... ... .. .. ..
        Waiver.objects.create(waiver_file=file, location=location, business_id=request.user.profile.business_id)

class ProfileCsvForm(forms.Form):
    """Define form to import customer profile csv."""

    csv_fields = [
        _("Email"), _("First Name"), _("Last Name"), _("Phone Number"), _("Gender"), _("DOB"),
        _("Profile Picture"), _("Street"), _("City"), _("State"), _("Country"),
        _("Emergency Contact Name"), _("Emergency Contact Relationship"),
        _("Emergency Contact Phone")
    ]
    required_fields = [str(_("Email"))]

    mapper = {
        _("Email"): "email",
        _("First Name"): "first_name",
        _("Last Name"): "last_name",
        _("Phone Number"): "phone",
        _("Gender"): "gender",
        _("DOB"): "date_of_birth",
        _("Profile Picture"): "profile_image_url",
        _("Street"): "street_address",
        _("City"): "city",
        _("State"): "state",
        _("Country"): "country",
        _("Emergency Contact Name"): "emgcy_cont_name",
        _("Emergency Contact Relationship"): "emgcy_cont_relation",
        _("Emergency Contact Phone"): "emgcy_cont_num"
    }

    is_csv_file = re.compile(".csv$", re.IGNORECASE)

    imported = forms.IntegerField(required=False)

    file = forms.FileField(
        widget=forms.FileInput(
            attrs={
                "name": "file"
            }
        ),
        required=True
    )

    record_limit = 10000

    class Meta:
        fields = ["file", "imported"]

    def __init__(self, *args, **kwargs):
        # Init stuffs
        self.file_name = None
        self.reader = None
        self.file_records = []

        # Init gender processor
        gender_choices = dict(Profile.GENDER_TYPE_CHOICES)
        self.gender_choices = {value: key for key, value in gender_choices.items()}
        for item in gender_choices.values():
            self.gender_choices[item.lower()] = self.gender_choices.get(item)
        
        # Try save request
        try:
            self.request = kwargs.pop("request")
        except Exception:
            self.request = None
        
        # Load super form
        super().__init__(*args, **kwargs)

    def has_csv_fields(self, columns: list) -> bool:
        """Return check if required field missing from column list."""
        # Get lower of csv fields
        csv_fields = [item.lower() for item in self.required_fields]
        lower_columns = [item.lower() for item in columns]

        # Loop check columns and field with case insensitive
        for column in csv_fields:
            if column in lower_columns:
                continue
            return False

        return True

    def clean(self):
        """Return action check validity of file data."""
        # Default clean input data
        self.cleaned_data = super().clean()

        # Get file name
        self.file_name = self.cleaned_data["file"].name.lower()

        # Validate extension
        if not self.is_csv_file.search(self.file_name):
            raise forms.ValidationError({
                "file": _("Wrong file format, only csv format accepted.")
            })

        # Load file data to csv reader
        try:
            file_string = self.cleaned_data["file"].file.read().decode("utf-8")
            self.reader = csv.DictReader(io.StringIO(file_string))
        except Exception:
            raise forms.ValidationError({
                "file": _("Wrong file format, only csv format accepted.")
            })

        # Validate required csv fields
        if not self.has_csv_fields(self.reader.fieldnames):
            raise forms.ValidationError(
                {
                    "file": _("Missing required csv fields: %s") % (
                        ", ".join(self.required_fields)
                    )
                }
            )

        # Load record and validate no record
        self.file_records = [row for row in self.reader]
        if not self.file_records:
            raise forms.ValidationError({
                "file": _("No record found.")
            })

        # Close file
        self.cleaned_data["file"].file.close()

        return self.cleaned_data

    def generate_record(self, record: dict):
        """Return status and object of saving record item to Profile table."""
        # Check for required fields
        for field in self.required_fields:
            if record.get(field) in ["", None]:
                return False, _("Missing required field: %s") % field

        # Validate gender if exist
        record_gender = record.get("Gender")
        if not record_gender or record_gender not in self.gender_choices:
            record["Gender"] = Profile.GENDER_TYPE_NOTLISTED
        else:
            record["Gender"] = self.gender_choices.get(record_gender)

        # Validate date of birth
        dob = record.get("DOB")
        if dob:
            try:
                datetime.strptime(dob, "%m/%d/%Y")
            except ValueError:
                return False, _("Incorrect date of birth format, should be MM/DD/YYYY")

        # Convert record to item
        item = {
            field: record.get(key) for key, field in self.mapper.items()
        }

        # Lower case email
        item["email"] = item.get("email").lower()

        # Append business id
        item["business_id"] = self.request.user.profile.business_id

        # Set user type
        item["user_type"] = Profile.USER_TYPE_CUSTOMER

        # Convert date format
        if item.get("date_of_birth"):
            item["date_of_birth"] = datetime.strptime(
                item.get("date_of_birth"), "%m/%d/%Y"
            )

        # Remove unset fields
        kwargs = {
            key: value for key, value in item.items()
            if value not in ["", None]
        }

        # Check duplicate
        instance = Profile.objects.only("id", "email", "business_id").filter(
            email=item.get("email"),
            business_id=item.get("business_id")
        )
        if instance:
            return False, "duplicate key value"

        # Save new instance
        try:
            instance = Profile.objects.create(**kwargs)
            return True, instance
        except Exception as err_msg:
            return False, str(err_msg)

    def save(self):
        """Save csv records."""
        # Generate fail record
        failed_records = []
        write_instances = []

        # Loop save through 
        for record in self.file_records:
            # Check status of trying save record
            status, instance = self.generate_record(record)

            # Append to pool
            if status is True:
                write_instances.append(instance)
            elif "duplicate key value" in instance.lower():
                record["Status"] = _("Record already exists.")
                failed_records.append(record)
            else:
                record["Status"] = _("Record failed.")
                failed_records.append(record)

        # Create file to save fail records
        file_name = None
        if failed_records:
            # Generate file params
            file_name = self.is_csv_file.sub(
                f"_{self.request.user.profile.business_id}_errors.csv",
                self.file_name
            )
            file_path = os.path.join(settings.MEDIA_ROOT, file_name)

            # Open file to write
            with open(file_path, "w+", encoding="utf-8", newline='') as file:
                # Load writer
                self.writer = csv.DictWriter(
                    file,
                    fieldnames=self.csv_fields + ["Status"],
                    extrasaction="ignore"
                )

                # Write headers
                self.writer.writeheader()

                # Write record
                for record in failed_records:
                    self.writer.writerow(record)


        return {
            "file": file_name,
            "imported": len(write_instances)
        }