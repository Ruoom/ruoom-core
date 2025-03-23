import os

from datetime import datetime

from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from django.http import JsonResponse

#from .models import ClassBookingCart
from administration.core.loading import get_model
from django.views.decorators.clickjacking import xframe_options_exempt
from administration.models import Location, Business
from ruoom.automated_email_system import automated_email_send

from django.template.loader import render_to_string

from django.conf import settings
from django.utils.translation import gettext_lazy as _

Profile = get_model("registration","Profile")
Location = get_model("administration", "Location")
Room = get_model("administration", "Room")

UPCOMING_CLASS_HOURS = 24
ALIGNMENT_TOLERANCE_FACTOR = 0.5
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ==========================
# Customer Account Template
# ==========================

class CustomerAccount(TemplateView):
    def get(self,request):
        return redirect('/customer/account_settings')

# ====================================
# Customer Accounts Settings Template
# ====================================


class CustomerAccountSettings(TemplateView):
    template_name = "customer/account_settings.html"

    context = {
        "customer_area_expand": "true",
        "customer_class_show": "show",
        "customer_account_settings": "active",
    }

    @xframe_options_exempt
    def get(self, request):
        customer_required = request.GET.get("customer")
        customer_business_number = request.user.profile.business_id #request.GET.get("customerBusinessNumber")

        location_list = Location.objects.filter(
            business_id=customer_business_number
        )
        self.context["location_list"] = location_list
        self.context["currency"] = Business.objects.get(business_id=customer_business_number).currency_symbol()
        if customer_required:
            request.session["admin_customer_control"] = customer_required
            profile = Profile.objects.filter(business_id=request.user.profile.business_id, id=customer_required).first()

            if profile:
                self.context["object"] = profile

                if (
                    profile.first_name
                    and profile.last_name
                    and profile.gender
                    and profile.date_of_birth
                ):
                    self.context["profile_info_updated"] = True
                else:
                    self.context["profile_info_updated"] = False

                if (
                    profile.street_address
                    and profile.city
                    and profile.state
                    and profile.emgcy_cont_name
                    and profile.emgcy_cont_num
                    and profile.emgcy_cont_relation
                ):
                    self.context["contact_info_updated"] = True
                else:
                    self.context["contact_info_updated"] = False

                if profile.email:
                    self.context["account_info_updated"] = True
                else:
                    self.context["account_info_updated"] = False
            self.context["gender_type_choices"] = Profile.GENDER_TYPE_CHOICES
            self.context["admin_customer"] = "true"
            self.context["customer_base_template"] = "administration/customers.html"
            self.context["customer_name"] = profile.localized_name()
            self.context["customer_id"] = customer_required
            self.context["customer_business_number"] = customer_business_number

            studio_obj = Business.objects.get(business_id=request.user.profile.business_id)
            self.context["business_name"] = studio_obj.name

            return render(request, self.template_name, self.context)

        profile = Profile.objects.filter(pk=request.user.id).first()
        if profile:
            self.context["object"] = profile

            if (
                profile.first_name
                and profile.last_name
                and profile.gender
                and profile.date_of_birth
            ):
                self.context["profile_info_updated"] = True
            else:
                self.context["profile_info_updated"] = False

            if (
                profile.street_address
                and profile.city
                and profile.state
                and profile.emgcy_cont_name
                and profile.emgcy_cont_num
                and profile.emgcy_cont_relation
            ):
                self.context["contact_info_updated"] = True
            else:
                self.context["contact_info_updated"] = False

            if profile.email:
                self.context["account_info_updated"] = True
            else:
                self.context["account_info_updated"] = False
        studio_obj = Business.objects.get(business_id=request.user.profile.business_id)
        self.context["business_name"] = studio_obj.name
        self.context["gender_type_choices"] = Profile.GENDER_TYPE_CHOICES
        self.context["admin_customer"] = "false"
        self.context["customer_base_template"] = "customer/customer_account.html"
        self.context["background_color"] = studio_obj.background_color
        self.context["button_text_color"] = studio_obj.button_text_color
        self.context["button_color"] = studio_obj.button_color
        self.context["text_color"] = studio_obj.text_color

        return render(request, self.template_name, self.context)


    def get_current_user(self, request):
        customer_required = request.session.get("admin_customer_control")
        if customer_required:
            profile = Profile.objects.filter(business_id=request.user.profile.business_id, id=customer_required).first()
            try:
                del request.session["admin_customer_control"]
            except KeyError:
                pass
            return profile
        return request.user

    def post(self, request):
        account_setting_user_obj = self.get_current_user(request=request)

        if "personal_info" in request.POST:
            print(request.POST)
            profile = Profile.objects.get(pk=account_setting_user_obj.id)
            profile.first_name = request.POST.get("first_name")
            profile.last_name = request.POST.get("last_name")
            profile.gender = request.POST.get("gender")
            profile.date_of_birth = (
                request.POST.get("date_of_birth")
                if request.POST.get("date_of_birth")
                else None
            )
            profile.save()
            return self.get(request)

        elif "contact_info" in request.POST:
            profile = Profile.objects.get(pk=account_setting_user_obj.id)
            profile.street_address = request.POST.get("street_address")
            profile.city = request.POST.get("city")
            profile.state = request.POST.get("state")
            profile.phone = request.POST.get("phone")
            profile.emgcy_cont_name = request.POST.get("emgcy_cont_name")
            profile.emgcy_cont_relation = request.POST.get("emgcy_cont_relation")
            profile.emgcy_cont_num = request.POST.get("emgcy_cont_num")
    

            if request.POST.get("message_consent"):
                profile.message_consent = request.POST.get("message_consent")
            else:
                profile.message_consent = 'False'
         
            profile.save()
            return self.get(request)

        elif "account_info" in request.POST:
            profile = Profile.objects.get(pk=account_setting_user_obj.id)
            profile.email = request.POST.get("email")
            if request.POST.get("password"):
                profile.set_password(request.POST.get("password"))
            if request.POST.get("default_location"):
                profile.default_location = Location.objects.get(id=int(request.POST.get('default_location'))) or None
            profile.save()

            return self.get(request)

        return redirect("customer:customer-account-settings")

# =====================

def ajax_for_get_profile_results(request):
    email = request.GET.get('email', None)
    profile = Profile.objects.filter(email=email, business_id=request.user.profile.business_id)
    if len(profile) > 0:
        context = {
            'first_name': profile.first().first_name,
            'last_name': profile.first().last_name,
            'id':profile.first().id
        }
    else:
        context = {
            'first_name': None,
            'last_name': None,
            'id':None
        }
    return JsonResponse(context)

def sort_times(times):
    # Define the format for parsing the time strings
    time_format = "%I:%M %p"
    
    # Parse the time strings into datetime objects
    parsed_times = [datetime.strptime(time, time_format) for time in times]
    
    # Sort the list of datetime objects
    sorted_times = sorted(parsed_times)

    # Convert the sorted datetime objects back to the original string format
    sorted_time_strings = [time.strftime(time_format) for time in sorted_times]

    return sorted_time_strings   