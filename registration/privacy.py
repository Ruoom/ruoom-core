from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone

from administration.core.loading import get_model


Profile = get_model("registration", "Profile")


def _anonymized_email(profile):
    return f"erased-user-{profile.business_id}-{profile.pk}@deleted.invalid"


def _clear_field_response_value(field_response):
    field_type = field_response.field_type()
    update_fields = []
    if field_type == "email" and field_response.value_email:
        field_response.value_email = ""
        update_fields.append("value_email")
    elif field_type == "phone" and field_response.value_phone:
        field_response.value_phone = ""
        update_fields.append("value_phone")
    elif field_type == "file":
        if field_response.value_file:
            storage_name = field_response.value_file.name
            field_response.value_file.delete(save=False)
            if storage_name and default_storage.exists(storage_name):
                default_storage.delete(storage_name)
        field_response.value_file = None
        field_response.value_file_original_name = ""
        field_response.value_file_content_type = ""
        field_response.value_file_size = None
        update_fields.extend(
            (
                "value_file",
                "value_file_original_name",
                "value_file_content_type",
                "value_file_size",
            )
        )
    elif field_type in {"text", "paragraph"}:
        label = (field_response.label() or "").strip().lower()
        if any(token in label for token in ("name", "email", "phone", "contact")):
            field_name = "value_text" if field_type == "text" else "value_paragraph"
            if getattr(field_response, field_name):
                setattr(field_response, field_name, "")
                update_fields.append(field_name)
    elif field_type == "date":
        label = (field_response.label() or "").strip().lower()
        if any(token in label for token in ("birth", "birthday", "dob")) and field_response.value_date:
            field_response.value_date = None
            update_fields.append("value_date")
    if update_fields:
        field_response.save(update_fields=tuple(update_fields))


@transaction.atomic
def erase_profile_personal_data(profile, erased_by=None):
    timestamp = timezone.now()
    anonymized_email = _anonymized_email(profile)

    if profile.profile_image:
        profile.profile_image.delete(save=False)

    profile.first_name = ""
    profile.last_name = ""
    profile.email = anonymized_email
    profile.username = Profile.username_for_identity(anonymized_email, profile.business_id)
    profile.phone = ""
    profile.notes = ""
    profile.gender = None
    profile.date_of_birth = None
    profile.profile_image_url = ""
    profile.profile_image = None
    profile.street_address = ""
    profile.city = ""
    profile.state = ""
    profile.country = ""
    profile.emgcy_cont_name = ""
    profile.emgcy_cont_relation = ""
    profile.emgcy_cont_num = ""
    profile.message_consent = False
    profile.default_location = None
    profile.is_active = False
    profile.is_staff = False
    profile.is_superuser = False
    profile.staff_is_active = False
    profile.personal_data_erased = True
    profile.personal_data_erased_at = timestamp
    profile.set_unusable_password()
    profile.save()
    profile.groups.clear()
    profile.user_permissions.clear()

    try:
        CustomerCheckin = get_model("booking", "CustomerCheckin")
        CustomerCheckin.objects.filter(customer=profile).update(
            guest_name_snapshot="Deleted User",
            guest_email_snapshot="",
        )
    except LookupError:
        pass

    try:
        CustomFormResponse = get_model("customforms", "CustomFormResponse")
        CustomFormFieldResponse = get_model("customforms", "CustomFormFieldResponse")
    except LookupError:
        return profile

    for response in CustomFormFieldResponse.objects.filter(form_response__customer=profile):
        _clear_field_response_value(response)

    CustomFormFieldResponse.objects.filter(customer=profile).update(customer=None)
    CustomFormResponse.objects.filter(customer=profile).update(customer=None, guest_email="")

    return profile
