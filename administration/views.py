from time import time as t_time
import json
from http import HTTPStatus
from datetime import datetime
import pytz
import csv
from django.conf import settings
from django.template.loader import render_to_string
from django.db.models import Q
from django.http import (
    HttpResponseRedirect,
    HttpResponse,
    Http404,
    StreamingHttpResponse,
    JsonResponse
)
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy

from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.contrib import messages
from django.utils.translation import pgettext, gettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from security.key_lock import RuoomSecurity

from registration.forms import *
from registration.models import *

from .forms import *
from .helpers import is_ajax
from ruoom.automated_email_system import automated_email_send

# from weasyprint import HTML
from django.template.loader import render_to_string

from .models import StudioSettings, Locations

from ruoom.settings import COUNTRY_LANGUAGES
import os

Profile = get_model("registration", "Profile")
Locations = get_model("administration", "Locations")
DaysOfOperation = get_model("administration", "DaysOfOperation")

# Create your views here.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEET_PER_METER = 3.28084

def read_file(filename):
    f = open(filename, 'r', encoding="utf-8")
    file_content = f.read()
    f.close()
    return file_content

def new_password_email_send(recipient_email,subject,customer_name,password_link,business_id=None):
    context = {
        'Customer_name': customer_name, 
        'password_link': password_link
    }

    html_content = render_to_string("../templates/emails/create-password.html", context)

    automated_email_send(recipient_email,subject,html_content,business_id)

    return JsonResponse({"message":"success"})

def reset_password_email_send(recipient_email,subject,customer,password_link,business_id=None):
    context = {
        'Customer': customer, 
        'password_link': password_link
    }
    html_content = render_to_string("../templates/emails/reset-password.html", context)

    automated_email_send(recipient_email,subject,html_content,business_id)

    return JsonResponse({"message":"success"})

def swap_request_email_send(recipient_email, subject, swap_request, shift_details, request, business_id=None):

    current_domain = 'http://{0}{1}'.format(request.get_host(),"/administration/download_swap_request_pdf")

    context = {
        'swap_request': swap_request, 
        'shift_details': shift_details, 
        'timestamp': datetime.now(), 
        "current_domain":current_domain,
        "message":subject
    }

    html_content = render_to_string("../templates/emails/staff-swap-request.html", context)

    automated_email_send([recipient_email],subject,html_content,business_id)

    return JsonResponse({"message":"success"})

def download_media(request, path):
    # Load file path
    file_path = os.path.join(
        settings.MEDIA_ROOT,
        path
    )

    # Check if file exist and return
    if os.path.exists(file_path):
        with open(file_path, "rb") as file:
            response = HttpResponse(
                file.read(),
                content_type="text/csv"
            )
            response["Content-Disposition"] = "inline; filename=%s" % (
                os.path.basename(file_path)
            )
            return response

    raise Http404

class Dashboard(TemplateView):
    template_name = 'administration/dashboard.html'

    def get(self, request):
        # Load params
        location_id = self.request.GET.get("location_id")

        # Prepare bar chart data for todays classes
        staff = request.user.profile

        # Load location filter
        location = None
        if staff.default_location and location_id is None:
            location = Locations.objects.get(pk=int(staff.default_location.id))
        if location is None and location_id is None:
             # Prepare classes
            classes_queries = Q(
                business_id=request.user.profile.business_id
            )

        if location is None:
            # Load location filter
            location = Locations.objects.filter(
                id=location_id,
                business_id=staff.business_id
            ).order_by('id').first()
            
        # Redirect if incorrect user type
        if not staff.user_type == Profile.USER_TYPE_STAFF:
            return redirect(settings.CUSTOMER_LOGIN_REDIRECT_URL)

        # Prepare list of locations
        location_list = Locations.objects.filter(business_id=staff.business_id)

        # Prepare task
        if location:
            #task_queries = task_queries & Q(location=location)
            tz = pytz.timezone(Locations.objects.get(id=location.id).time_zone_string)
        else:
            if Locations.objects.filter(business_id=request.user.profile.business_id):
                tz = pytz.timezone(Locations.objects.filter(business_id=request.user.profile.business_id).first().time_zone_string)
            else:
                tz = pytz.utc

        if location:
            classes_queries = classes_queries & Q(
                Q(room__location=location)
                | Q(layout__room__location=location)
                | Q(location_ref=location)
            )


        # Generate context
        context = {
            "dashboard": "active",
            "location_list": location_list,
            "location": location,
            'greeting_char': pgettext("Character after greeting person by name", " "),
            'date': datetime.now().astimezone(tz).date()
        }

        return render(request, self.template_name, context=context)

class CustomerOptions(TemplateView):
    template_name = "administration/customer_info_nav.html"
    context = {}

    def get(self, request):
        if request.GET.get("customer"):
            self.context["admin_customer_modify"] = "true"
            self.context["customer"] = request.GET.get("customer")
            self.context["customer_name"] = request.GET.get("customerName")
            self.context["customer_email"] = request.GET.get("customerEmail")
            self.context["customer_business_number"] =request.GET.get("customerBusinessNumber")
            self.context["customer_base_template"] = "administration/customers.html"
            return render(request, self.template_name, self.context)

class CustomerPage(FormView):
    template_name = "administration/customers.html"

    def get(self, request, customer_form=None):
        if not customer_form:
            customer_form = CreateCustomerForm()
        csv_form = ProfileCsvForm()
        business_id = request.user.profile.business_id
        studio_settings = StudioSettings.objects.filter(business_id=business_id).first()
        default_country_code = (
            studio_settings.default_country_code if studio_settings else "us"
        )
        customers = Profile.objects.filter(
            Q(user_type=Profile.USER_TYPE_CUSTOMER) | Q(user_type=Profile.USER_TYPE_STAFF),
            business_id=business_id
        ).order_by("first_name")
        args = {
            "customerspage": "active",
            "csv_form": csv_form,
            "customer_form": customer_form,
            "default_country_code": default_country_code,
            "customers": customers,
        }
        return render(request, self.template_name, args)

    def post(self, request):
        if "new_customer" in request.POST:
            # Load form
            updated_request = request.POST.copy()
            updated_request["phone"] = updated_request["phone_with_code"]
            check_exist = Profile.objects.filter(
                Q(user_type=Profile.USER_TYPE_CUSTOMER) | Q(user_type=Profile.USER_TYPE_STAFF),
                email = updated_request["email"],
                business_id=request.user.profile.business_id)
            form = CreateCustomerForm(updated_request)
            if not check_exist:
                # Check valid form
                if form.is_valid():
                    form.save(request, request.user.profile.business_id)
                    return self.get(request)
            else:
                form.add_error('email', _("A user with this email already exists"))

            # Re render form if not valid
            args = {"customer_form": form, "open_customer_modal": "true"}
            return render(request, self.template_name, args)

        elif "new_csv" in request.POST:
            # Load form
            form = ProfileCsvForm(
                request.POST,
                request.FILES,
                request=request
            )

            # Check valid csv and message errors
            if not form.is_valid():
                for errors in form.errors.values():
                    for error_msg in errors:
                        messages.error(request, error_msg)
                return self.get(request)

            # Do import csv and report result
            form_result = form.save()
            imported = form_result.get("imported")
            fail_file = form_result.get("file")

            # Message import result
            messages.success(request, _(f"{imported} customer(s) imported succesfully."))
            if fail_file is not None:
                # Init link to file
                fail_url = reverse_lazy(
                    "administration:download_media",
                    args=[fail_file]
                )

                # Add message fail file
                messages.error(
                    request,
                    ''.join([f"<a href=\"{fail_url}\">",str(_("Please check this file for invalid data.")),"</a>"]),
                    extra_tags="safe"
                )

            return self.get(request)
        elif "download_csv" in request.POST:
            return redirect("administration:export_profile")
        elif is_ajax(request):
            response = {}
            customer_id = request.POST.get("customer_id")
            customer_instance = get_object_or_404(Profile, id=customer_id)
            customer_form = UpdateCustomerForm(
                request.POST or None, instance=customer_instance
            )
            if customer_form.is_valid():
                customer_form.save()
                response = {"success": _("Successfully Updated")}
            else:
                response["error"] = customer_form.errors
            return JsonResponse(response)

def no_location(request):
    return render(request, 'administration/no_location_message.html')

class Schedule(TemplateView):
    template_name = 'administration/schedule.html'

    def get(self, request):
        # Load form and stuffs
        business_id = request.user.profile.business_id
        data_dict = request.session.get('saved')

        # Load staff profile
        staff = request.user.profile

        # Load Location
        location_id = self.request.GET.get("location_id")
        if not(location_id) or location_id == '': #if no location, assume first location at the business
            loc = Locations.objects.filter(business_id=request.user.profile.business_id).first()
            if loc:
                location_id = loc.id
            else:
                location_id = 0

        location = None
        if staff.default_location and location_id is None:
            location = Locations.objects.get(pk=int(staff.default_location.id))
        
        if location is None:
            # Load location filter
            location = Locations.objects.filter(
                id=location_id,
                business_id=staff.business_id
            ).order_by('id').first()

        # Prepare list of locations
        location_list = Locations.objects.filter(business_id=staff.business_id)

        # Hours other than business hours are dimmed if these settings are available in calendar
        business_hours = {}
        if location:
            days_of_week = location.daysofoperation_set.filter(is_checked=True).values_list('day_of_week')
            days_of_week = [DaysOfOperation.days.get(day) for day in days_of_week]
        else:
            days_of_week = list(DaysOfOperation.days.values())

        # Load business hour
        start_time = _(location.business_hours_from if location else _('12am'))
        end_time = _(location.business_hours_to if location else _('11pm'))

        if request.user.profile.language == Profile.LANGUAGE_ENGLISH:
            start_time = start_time.replace(' ', '').lower()
            end_time = end_time.replace(' ', '').lower()

        business_hours = {
            'start_time': start_time,
            'end_time': end_time,
            'days_of_week': days_of_week
        }

        if not location:
            return redirect('/administration/nolocation')
        else:
            tz = Locations.objects.get(id=location_id).time_zone_string

            # Prepare context arguments
            args = {
                "location": location,
                "location_list": location_list,
                'class_highlight_color': 'green',
                'table_grid_thickness': '1px',
                'table_border_color': '#ddd',
                'class_text_color': 'white',
                'class_block_color': '#43C3EF',
                'show_all_day_bar': False,
                'business_hours': business_hours,
                "data_dict":data_dict,
                'schedule':'active',
                'locationTimezone': tz,
                'business_id': business_id,
            }
     
            return render(request, self.template_name, args)

class StaffPage(TemplateView):
    template_name = 'administration/staff.html'

    def get(self, request):
        staff_form = CreateStaffForm()
        args = {
            'staffpage': "active",
            'staff_form': staff_form,
        }
        return render(request, self.template_name, args)

    def post(self, request):
        location_id = request.POST.get('location_id',None)
        if not(location_id) or location_id == '': #if no location, assume first location at the business
            location_id = Locations.objects.filter(business_id=request.user.profile.business_id).first().id     #MAKE THIS PAGE HAVE LOCATION ID
        
        tz = pytz.timezone(Locations.objects.get(id=location_id).time_zone_string)

        if 'new_staff' in request.POST:
            form = CreateStaffForm(request.POST)
            if form.is_valid():
                form.save(request)
                return self.get(request)
            else:
                args = {'staff_form': form}
                return render(request, self.template_name, args)
        elif is_ajax(request):
            response = {}
            staff_id = request.POST.get('staff_id')
            staff_instance = get_object_or_404(Staff, id=staff_id)
            staff_form = UpdateStaffForm(
                request.POST or None, instance=staff_instance)
            if staff_form.is_valid():
                staff_form.save()
                response = {"success": "Successfully Updated"}
            else:
                response["error"] = staff_form.errors
            return JsonResponse(response)

class Help(TemplateView):
    template_name = 'administration/help-center.html'

    def get(self, request):
        context = {
            "password_reset_link": request.META.get('HTTP_HOST', '')+"/accounts/password_reset"
        }
        return render(request, self.template_name, context)

class HelpEmbed(TemplateView):
    template_name = 'administration/help-center-embed.html'

    def get(self, request):
        return render(request, self.template_name)

class HelpEmail(TemplateView):
    template_name = 'administration/help-center-emails.html'

    def get(self, request):
        return render(request, self.template_name)

class Config(FormView):
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(Config, self).dispatch(request, *args, **kwargs)

    template_name = 'administration/configuration.html'
    px_per_unit = 20
    alignment_factor = 1
    shape_type = 'span'

    def get(self, request,*args, **kwargs):
    
        business_id = request.user.profile.business_id

        if request.GET.get('split_location'):
            location_id = request.GET.get('split_location')
            update_location = Locations.objects.get(id=location_id)
            edit_form = CreateLocationForm(instance=update_location) 
            return HttpResponse(edit_form.as_p())

        elif request.GET.get('split_room'):
            room_id = request.GET.get('split_room')
            update_room = Rooms.objects.get(id=room_id)
            room_edit_form = CreateRoomForm(business_id=business_id,instance=update_room)
            return HttpResponse(room_edit_form.as_p())
        
        else:

            loc_form = CreateLocationForm()
            room_form = CreateRoomForm(business_id=business_id)
            locations = Locations.objects.filter(business_id=business_id)

            business_obj = StudioSettings.objects.get(business_id=business_id)
            default_location = business_obj.default_country_code

            args = {
                'roomo': 'active',
                'px_per_unit': self.px_per_unit,
                'loc_form': loc_form,
                'room_form': room_form,
                'locations': locations,
                'rooms': Rooms.objects.filter(location__in=locations),
                'default_location': default_location,
                'currency': business_obj.currency()
            }

            return render(request, self.template_name, args)
    
    
    def post(self, request,*args, **kwargs):
        if 'new_location' in request.POST:
            form = CreateLocationForm(request.POST)
            print(form.errors)
            if form.is_valid():
                new_location_instance = form.save()
                new_location_instance.business_id = request.user.profile.business_id
                obj = StudioSettings.objects.filter(business_id=new_location_instance.business_id).first()
                new_location_instance.country_code = obj.default_country_code
                for i in range(1,8):
                    new_day_of_operation = DaysOfOperation.objects.create(day_of_week=i, location=new_location_instance)
                    if DaysOfOperation.days.get(i) in request.POST:
                        new_day_of_operation.is_checked = True
                    new_day_of_operation.save()
                new_location_instance.save()
                
                return self.get(request)
            else:   
                return HttpResponseRedirect('/unsuccess/')
        
        elif 'edit_location' in request.POST:
            edit_locid = request.POST.get('edit_form_id')
            if edit_locid:
                edit_obj = get_object_or_404(Locations, pk=edit_locid)
                if edit_obj:
                    form = CreateLocationForm(request.POST, instance=edit_obj) 
                 
                    if form.is_valid():  
                        form.save()
                        return redirect('/administration/planner') 

            response = {
                'status': _('Error while updating Shift'),
                'ok': False,
                'errors': form.errors
            }
            return JsonResponse(response, status=HTTPStatus.BAD_REQUEST)

        elif 'edit_room' in request.POST:
            room_id = request.POST.get('edit_room_id')
            if room_id:
                room_obj = get_object_or_404(Rooms, pk=room_id)
                if room_obj:
                    form = CreateRoomForm(request.user.profile.business_id,request.POST, instance=room_obj) 
                    if form.is_valid():  
                        new_shift_instance = form.save()
                        new_shift_instance.save()
                        return redirect('/administration/planner') 

            response = {
                'status': _('Error while updating Shift'),
                'ok': False,
                'errors': form.errors
            }
            return JsonResponse(response, status=HTTPStatus.BAD_REQUEST)

        elif 'new_room' in request.POST:
            form = CreateRoomForm(request.user.profile.business_id, request.POST)
            if form.is_valid():
                new_room_instance = form.save()
                new_room_instance.business_id = request.user.profile.business_id

                country = StudioSettings.objects.get(business_id=request.user.profile.business_id).default_country_code
                if country == "kr":   #Convert meters to feet for storage
                    length = float(request.POST.get('length'))
                    width = float(request.POST.get('width'))
                    new_room_instance.length = length * FEET_PER_METER
                    new_room_instance.width = width * FEET_PER_METER

                new_room_instance.save()

                
                return self.get(request)
            else:
                return HttpResponseRedirect('/unsuccess/')

class Admin(TemplateView):
    template_name = 'administration/admin.html'

    def get(self, request):
        staff_id = request.GET.get('staff_id')
        if request.GET.get('TYPE') == 'get_staff_data':
            staff_obj = Profile.objects.filter(id=staff_id)[0]
            form = UpdateUserForm(instance=staff_obj, initial={'permissions': list(staff_obj.groups.all())})
         
            return HttpResponse(form.as_p())
        elif is_ajax(request):
            if request.GET.get('TYPE') == 'delete_user' and is_ajax(request):
                print("Deleting Staff User!")
                staff_id = request.GET.get('staff_id')
                staff_obj = get_object_or_404(Staff, pk=staff_id)
                if staff_obj:
                    staff_obj.delete()
                    response = {
                        'ok': True,
                        'status': 'deleted'
                    }
                    return JsonResponse(response)
                response = {
                    'ok': True,
                    'status': _('Error while downloading, please try again')
                }
                return JsonResponse(response)
        else:
            user_form = CreateUserForm(user=request.user)         
            edit_user_form = UpdateUserForm(user=request.user)
           
            staffs = Profile.objects.filter(
                user_type=Profile.USER_TYPE_STAFF,
                business_id=request.user.profile.business_id
            )
            args = {
                'permissions': 'active',
                'user_form': user_form,
                'edit_user_form': edit_user_form,
                'staffs': staffs,
                'username': request.user.profile.email
            }
            return render(request, self.template_name, args)

    def post(self, request):
        if 'new_user' in request.POST:
            # Init create kwargs
            profile = getattr(request.user, "profile", None)
            create_user_args = {
                "user": request.user
            }
            if profile and profile.business_id:
                create_user_args["business_id"] = profile.business_id

            # Handle form
            create_form = CreateUserForm(request.POST, **create_user_args)
            if create_form.is_valid():
                new_user = create_form.save(request)
                new_user.business_id = request.user.profile.business_id
                new_user.password = "rl9HYY*ou0R4sWh&w3D6E#5*oC#"       #This password will be reset immediately, and isn't salted with encryption so is impossible to replicate
                obj = StudioSettings.objects.filter(business_id=new_user.business_id).first()
                new_user.language = COUNTRY_LANGUAGES.get(obj.default_language(), "en")
                new_user.save()

                current_domain = request.META.get('HTTP_HOST', '')
                response = reset_password_email_send([new_user.email],_("Ruoom - New Account Creation & Set New Password"),new_user,current_domain+"/accounts/password_reset")

                return redirect('administration:admin')
            else:
                staffs = Profile.objects.filter(user_type=Profile.USER_TYPE_STAFF, business_id=request.user.profile.business_id)
                args = {'user_form': create_form,
                        'edit_user_form': UpdateUserForm(),
                        'showCreateUserForm': True,
                        'staffs': staffs}
                return render(request,
                              self.template_name,
                              args,
                              status=HTTPStatus.BAD_REQUEST)
        elif 'update_user' in request.POST:
            user_id = request.POST.get('user_id')
            if user_id:
                staff_obj = get_object_or_404(Staff, pk=user_id)
                update_form = UpdateUserForm(
                    request.POST,
                    user=request.user,
                    instance=staff_obj
                )

                if update_form.is_valid():
                    update_form.save()
                    data = {
                        'showEditUserForm': True,
                        'status': 'updated',
                    }
                    return HttpResponseRedirect(reverse_lazy('administration:admin'))
                else:
                    # add add user form or find a way to reutrn with just errors.
                    data = {
                        'showEditUserForm': True,
                        'status': 'form_error',
                        'errors': update_form.errors
                    }
                    return JsonResponse(data, status=HTTPStatus.OK)

            return JsonResponse({'status': 'error','ok': False}, status=HTTPStatus.BAD_REQUEST)
        elif 'reset_password' in request.POST:
            staff_reset_id = request.POST.get('reset-id')
            staff_to_reset = Profile.objects.get(id=staff_reset_id)
            current_domain = request.META.get('HTTP_HOST', '')

            response = reset_password_email_send([staff_to_reset.email],_("Ruoom - Reset Password Request"),staff_to_reset,current_domain+"/accounts/password_reset")

            return redirect('administration:admin')

        elif 'delete_user' in request.POST:
            print("Downgrading User from Staff to Customer!")
            staff_id = request.POST.get('staff_id')
            staff_obj = get_object_or_404(Profile, pk=staff_id)
            if staff_obj:
                staff_obj.user_type = Profile.USER_TYPE_CUSTOMER
                staff_obj.save()
            return redirect('administration:admin')
        else:
            return redirect('administration:admin')
        
        return redirect('administration:admin')

def settingsEmbed(request):
    template_name = 'administration/settings-embed.html'
    settings = Settings()
    url = "administration:settings-embed"
    if request.method == 'GET':
        return settings.get(request=request,template_name=template_name)
    if request.method == 'POST':
        return settings.post(request=request,url=url)
    else:
        return HttpResponseRedirect('/unsuccess/')
        
def settingsContact(request):
    template_name = 'administration/settings-contact.html'
    settings = Settings()
    url = "administration:settings-contact"
    if request.method == 'GET':
        return settings.get(request=request,template_name=template_name)
    if request.method == 'POST':
        return settings.post(request=request,url=url)
    else:
        return HttpResponseRedirect('/unsuccess/')

class Settings(TemplateView):
    ruoom_security = RuoomSecurity()

    def get(self, request, template_name=None):
        if not template_name:
            return redirect(reverse_lazy("administration:settings-embed"))
        self.context = {}
        obj = StudioSettings.objects.filter(business_id=request.user.profile.business_id).first()
        
        if obj:
            self.context["obj"] = obj
            self.set_color_to_context(studio_setting_obj=obj)
            self.set_email_information_to_context(studio_setting_obj=obj)
            self.set_business_information_to_context(studio_setting_obj=obj)

        current_domain = request.META.get('HTTP_HOST', '')
        self.context["domain"] = current_domain
        self.context["business_id"] = request.user.profile.business_id

        return render(request, template_name, self.context)

    def post(self, request, url):
        self.context = {}
        obj_list = StudioSettings.objects.filter(business_id=request.user.profile.business_id)
        
        setting_update = request.POST.get("setting_update")

        if obj_list.exists():
            obj = obj_list.first()
      
        else:
            obj = StudioSettings.objects.create(
                name="NEW OBJ CREATED ON SETTINGS PAGE, REPORT", business_id=request.user.profile.business_id
            )

        self.context["obj"] = obj

        if setting_update == "colours_settings":
            self.set_colors(request_dict=request, studio_settings_obj=obj)

        elif setting_update == "email_settings":
            self.set_email_information(request_dict=request, studio_settings_obj=obj)
        elif setting_update == "business_settings":
            self.set_business_information(request_dict=request, studio_settings_obj=obj)

        messages.info(
            request,
            "{0} Settings successfully saved and profile updated!".format(
                setting_update
            ),
        )
        return redirect(reverse_lazy(url))

    def set_color_to_context(self,studio_setting_obj):
        """
        this method is responsible for setting the colors to context which is then used by
        html file to render values
        following colors are used by 'administration/settings.html'

        - header color
        - button color
        - text color
        - background color

        Args:
            studio_setting_obj (type = StudioSettings object): StudioSettings model object
        """
        self.context["header_color"] = studio_setting_obj.header_color
        self.context["button_color"] = studio_setting_obj.button_color
        self.context["text_color"] = studio_setting_obj.text_color
        self.context["background_color"] = studio_setting_obj.background_color
        self.context["button_text_color"] = studio_setting_obj.button_text_color

    def set_email_information_to_context(self,studio_setting_obj):
        """
        this method is responsible for setting the colors to context which is then used by
        html file to render values
        following colors are used by 'administration/settings.html'

        - Email Address
        - Applicaiton Password
        - Host Address
        - Host Port
        - Host using TLS?

        Args:
            studio_setting_obj (type = StudioSettings object): StudioSettings model object
        """
        self.context["email_address"] = studio_setting_obj.email_address
        if studio_setting_obj.application_password:
            try:
                self.context["application_password"] = self.ruoom_security.decrypt_message(encrypted_message=studio_setting_obj.application_password)
            except:
                self.context["application_password"] = studio_setting_obj.application_password
        else:
            self.context["application_password"] = studio_setting_obj.application_password
        self.context["host_address"] = studio_setting_obj.host_address
        self.context["host_port"] = studio_setting_obj.host_port
        self.context["host_tls"] = studio_setting_obj.host_tls

    def set_business_information_to_context(self,studio_setting_obj):
        """
        this method is responsible for setting the colors to context which is then used by
        html file to render values
        following colors are used by 'administration/settings.html'

        - contact email
        - business website

        Args:
            studio_setting_obj (type = StudioSettings object): StudioSettings model object
        """
        if studio_setting_obj.name:
            self.context["business_name"] = studio_setting_obj.name
        else:
            self.context["business_name"] = ""
        if studio_setting_obj.business_website:
            self.context["business_website"] = studio_setting_obj.business_website
        else:
            self.context["business_website"] = ""
        if studio_setting_obj.contact_email:
            self.context["contact_email"] = studio_setting_obj.contact_email
        else:
            self.context["contact_email"] = ""

        if studio_setting_obj.contact_phone:
            self.context["contact_phone"] = studio_setting_obj.contact_phone
        else:
            self.context["contact_phone"] = ""

        if studio_setting_obj.business_address:
            self.context["business_address"] = studio_setting_obj.business_address
        else:
            self.context["business_address"] = ""

        if studio_setting_obj.business_registration_number:
            self.context["business_reg_id"] = studio_setting_obj.business_registration_number
        else:
            self.context["business_reg_id"] = ""
 
        if studio_setting_obj.business_owner:
            self.context["business_owner"] = studio_setting_obj.business_owner
        else:
            self.context["business_owner"] = ""

    def set_email_information(self, request_dict, studio_settings_obj):
        """
        this method will set email inforamtion under the "StudioSettings"
        we mainly have colors for
        - Email Address
        - Applicaiton Password
        - Host Address
        - Host Port
        - Host using TLS?

        Args:
            request_dict (type = request dict ): its the request information which comes with every request
            studio_settings_obj (type = StudioSettings object):  StudioSettings model object
        """
        email_address, application_password, host_address, host_port, host_tls = (
            request_dict.POST.get("email_address"),
            request_dict.POST.get("application_password"),
            request_dict.POST.get("host_address"),
            request_dict.POST.get("host_port"),
            request_dict.POST.get("host_tls"),
        )
        studio_settings_obj.email_address = email_address
        # studio_settings_obj.application_password = application_password
        studio_settings_obj.application_password = self.ruoom_security.process_encryption(
                encryption_value=application_password
            )
        studio_settings_obj.host_address = host_address
        studio_settings_obj.host_port = host_port
        if host_tls == "on":
            studio_settings_obj.host_tls = True
        else:
            studio_settings_obj.host_tls = False
        studio_settings_obj.save()

    def set_business_information(self, request_dict, studio_settings_obj):
        """
        this method will set email inforamtion under the "StudioSettings"
        we mainly have colors for
        - Business Email Address
        - Business Website
        - Business Address
        - Business Registration ID
        
        Args:
            request_dict (type = request dict ): its the request information which comes with every request
            studio_settings_obj (type = StudioSettings object):  StudioSettings model object
        """
        if request_dict.POST.get("business_name"):
            studio_settings_obj.name = request_dict.POST.get("business_name")

        if request_dict.POST.get("business_website"):
            studio_settings_obj.business_website = request_dict.POST.get("business_website")

        if request_dict.POST.get("contact_email"):
            studio_settings_obj.contact_email = request_dict.POST.get("contact_email")
        
        if request_dict.POST.get("contact_phone"):
            studio_settings_obj.contact_phone = request_dict.POST.get("contact_phone")
                                                                         
        if request_dict.POST.get("business_address"):
            studio_settings_obj.business_address = request_dict.POST.get("business_address")

        if request_dict.POST.get("business_reg_id"):
            studio_settings_obj.business_registration_number = request_dict.POST.get("business_reg_id")

        if request_dict.POST.get("business_owner"):
            studio_settings_obj.business_owner = request_dict.POST.get("business_owner")

        print(request_dict.POST.get("show_contact"))
        studio_settings_obj.show_contact = (request_dict.POST.get("show_contact") == "on")

        studio_settings_obj.save()
          
    def set_colors(self, request_dict, studio_settings_obj):
        """
        this method will set colors under the "StudioSettings"
        we mainly have colors for
        1.header
        2.button
        3.text
        4.background

        Args:
            request_dict (type = request dict ): its the request information which comes with every request
            studio_settings_obj (type = StudioSettings object):  StudioSettings model object
        """
        header_value, button_value, text_value, background_value, button_text_color = (
            request_dict.POST.get("headerValue"),
            request_dict.POST.get("buttonValue"),
            request_dict.POST.get("textValue"),
            request_dict.POST.get("backgroundValue"),
            request_dict.POST.get("buttonTextColor"),
        )
        studio_settings_obj.header_color = header_value
        studio_settings_obj.button_color = button_value
        studio_settings_obj.text_color = text_value
        studio_settings_obj.background_color = background_value
        studio_settings_obj.button_text_color = button_text_color
        studio_settings_obj.save()

class CustomersSearch(View):

    def get(self, request, *args, **kwargs):
        if is_ajax(request):
            name = request.GET.get('term', '')
            search_qs = Profile.objects.filter(
                Q(user_type=Profile.USER_TYPE_CUSTOMER) | Q(user_type=Profile.USER_TYPE_STAFF),
                Q(first_name__icontains=name) | Q(last_name__icontains=name),
                business_id=request.user.profile.business_id
            ).order_by('first_name')[:10]
            results = []
            for customer in search_qs:
                obj = {
                    "id": customer.id.__str__(),
                    "email": customer.email.__str__(),
                    "phone": customer.phone.__str__(),
                    "emgcy_cont_name": customer.emgcy_cont_name.__str__(),
                    "emgcy_cont_num": customer.emgcy_cont_num.__str__(),
                    "first_name": customer.first_name.__str__(),
                    "last_name": customer.last_name.__str__(),
                    "localized_name": customer.localized_name(),
                    "gender": customer.gender.__str__(),
                    "dob": customer.get_date_of_birth().__str__(),
                    "street_address": customer.street_address.__str__(),
                    "city": customer.city.__str__(),
                    "state": customer.state.__str__(),
                    "label": customer.first_last().__str__(),
                    "value": customer.first_last().__str__(),
                }
                results.append(obj)
            data = json.dumps(results)
        else:
            data = _('Not an Ajax Request')
        mimetype = 'application/json'
        return HttpResponse(data, mimetype)

class StaffSearch(View):

    def get(self, request, *args, **kwargs):
        if is_ajax(request):
            name = request.GET.get('term', '')
            search_qs = Profile.objects.filter(
                first_name__istartswith=name,
                user_type=Profile.USER_TYPE_STAFF,
                business_id=request.user.profile.business_id).order_by('first_name')[:10],
            results = []
            for staff in search_qs[0]:
                list_of_classes = []
                if staff.is_teacher:
                    staff_classes = staff.instructor_of.all()
                    for staff_class in staff_classes:
                        staff_class_data = {
                            "schedule_time": datetime.strftime(staff_class.scheduled_time, '%b %d, %Y, %H:%M:%S'),
                            "class_type": staff_class.class_type.name,
                        }
                        list_of_classes.append(staff_class_data)
                obj = {
                    "id": staff.id.__str__(),
                    "email": staff.email.__str__(),
                    "phone": staff.phone.__str__(),
                    "emgcy_cont_name": staff.emgcy_cont_name.__str__(),
                    "emgcy_cont_num": staff.emgcy_cont_num.__str__(),
                    "first_name": staff.first_name.__str__(),
                    "last_name": staff.last_name.__str__(),
                    "label": staff.first_last().__str__(),
                    "value": staff.first_last().__str__(),
                    "is_teacher": staff.is_teacher.__str__(),
                    "classes": list_of_classes.__str__()
                }
                results.append(obj)
            data = json.dumps(results)
        else:
            data = _('Not an Ajax Request')
        mimetype = 'application/json'
        return HttpResponse(data, mimetype)

class CustomerSearch(View):
    def get(self, request, *args, **kwargs):
        if is_ajax(request):
            name = request.GET.get('term', '')
            search_qs = Profile.objects.filter(
                first_name__istartswith=name, user_type=Profile.USER_TYPE_STUDENT,
                business_id=request.user.profile.business_id).order_by('first_name')[:10] \
                        | Profile.objects.filter( first_name__istartswith=name,
                                                user_type=Profile.USER_TYPE_STAFF,
                                                business_id=request.user.profile.business_id).order_by('first_name')[:10]

            results = []
            for student in search_qs:
                list_of_classes = []
                enrolled_classes = student.enrolled_classes.all()
                for enrolled_class in enrolled_classes:
                    enrolled_class_data = {
                        "schedule_time": datetime.strftime(enrolled_class.scheduled_time, '%b %d, %Y, %H:%M:%S'),
                        "class_type": enrolled_class.class_type.name,
                        "teacher": enrolled_class.teacher.first_name + " " + enrolled_class.teacher.last_name
                    }
                    list_of_classes.append(enrolled_class_data)

                obj = {
                    "id": student.id.__str__(),
                    "email": student.email.__str__(),
                    "phone": student.phone.__str__(),
                    "emgcy_cont_name": student.emgcy_cont_name.__str__(),
                    "emgcy_cont_num": student.emgcy_cont_num.__str__(),
                    "first_name": student.first_name.__str__(),
                    "last_name": student.last_name.__str__(),
                    "label": student.first_last_user().__str__(),
                    "value": student.first_last_user().__str__(),
                    "classes": list_of_classes.__str__(),
                    "user_type": student.user_type.__str__()
                }
                results.append(obj)
            data = json.dumps(results)

        else:
            data = _('Not an Ajax Request')
        mimetype = 'application/json'
        return HttpResponse(data, mimetype)

class ProfileSearch(View):

    def get(self, request, *args, **kwargs):
        if is_ajax(request):
            name = request.GET.get('term', '')
            search_qs = Profile.objects.filter(
                first_name__istartswith=name,
                business_id=request.user.profile.business_id).order_by('first_name')[:10]
            results = []
            for profile in search_qs:
                list_of_classes = []
                enrolled_classes = profile.enrolled_classes.all()
                for enrolled_class in enrolled_classes:
                    enrolled_class_data = {
                        "schedule_time": datetime.strftime(enrolled_class.scheduled_time, '%b %d, %Y, %H:%M:%S'),
                        "class_type": enrolled_class.class_type.name,
                        "teacher": enrolled_class.get_instructor()
                    }
                    list_of_classes.append(enrolled_class_data)
                obj = {
                    "id": profile.id.__str__(),
                    "email": profile.email.__str__(),
                    "phone": profile.phone.__str__(),
                    "credit": profile.credit.__str__(),
                    "emgcy_cont_name": profile.emgcy_cont_name.__str__(),
                    "emgcy_cont_num": profile.emgcy_cont_num.__str__(),
                    "first_name": profile.first_name.__str__(),
                    "last_name": profile.last_name.__str__(),
                    "label": profile.first_last().__str__(),
                    "value": profile.first_last().__str__(),
                    "classes": list_of_classes.__str__(),

                }
                results.append(obj)
            data = json.dumps(results)
        else:
            data = _('Not an Ajax Request')
        mimetype = 'application/json'
        return HttpResponse(data, mimetype)

class LanguageSelect(FormView):
    def get(self, request):
        #This get request finds the list of languages
        languages = Profile.LANGUAGES
        response = {
            'status': 'success',
            'languages': languages
        }
        return JsonResponse(response)

    def post(self, request):
        if 'language_select_form' in request.POST:
            language = request.POST.get('language')
            print("Changing user to language " + language)
            Profile.objects.filter(pk=request.user.id).update(language=language)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def ajax_for_selected_room_on_modal(request):
    room_id = request.GET.get('room_id', None)
    rooms = Rooms.objects.filter(id=room_id)

    country = StudioSettings.objects.get(business_id=request.user.profile.business_id).default_country_code

    if len(rooms) > 0:
        rooms = rooms.first()
        if country == "kr":
            context = {
                'dimensions': str(round(Decimal(rooms.length/FEET_PER_METER),1)) + str(_(" meters x ")) + str(round(Decimal(rooms.width/FEET_PER_METER),1)) + str(_(" meters"))
            }        
        else:
            context = {
                'dimensions': str(rooms.length) + str(_(" feet x ")) + str(rooms.width) + str(_(" feet"))
            }
    return JsonResponse(context)

class UploadWaiverView(View):
    def post(self, request):
        form = UploadWaiverForm(request.POST)
        if form.is_valid():
            form.save(request)
            return redirect('administration:configuration')

class StaffPage(TemplateView):
    template_name = 'administration/staff.html'

    def get(self, request):
        profile = Profile.objects.filter(pk=request.user.id).first()
        staff_member = Profile.objects.filter(user_type='staff', business_id=request.user.profile.business_id)
        locations = Locations.objects.filter(business_id=request.user.profile.business_id)
        user_form = CreateUserForm()
        context = {
            'staff': 'active',
            'staff_member':staff_member,
            'user_form': user_form,
            'profile':profile,
            'locations': locations
        }
        return render(request, self.template_name,context)

    def post(self, request):
        form = CreateUserForm(request.POST)
        if form.is_valid():
            staff_users_count = Profile.objects.filter(business_id=request.user.profile.business_id, user_type="staff").count()
            staff_user_subscription = StudioSettings.objects.get(business_id=request.user.profile.business_id).staff_user_subscription
            if staff_users_count >= staff_user_subscription:
                messages.info(request, _('Staff members limit reached. Please update you subscription to add more staff members.'))
                return redirect('administration:staff')
            new_user = form.save(request)
            new_user.business_id = request.user.profile.business_id
            new_user.save()
            messages.success(request, _('New Staff Member Created'))
            return redirect('administration:staff')
        else:
            staff_member = Profile.objects.filter(user_type='staff', business_id=request.user.profile.business_id)
            args = {'user_form': form,
                    'showCreateUserForm': True, 'staff_member': staff_member}
            return render(request, self.template_name, args, status=HTTPStatus.BAD_REQUEST)

class ExportProfile(View):

    field_converter = {
        "Email": "email",
        "First Name": "first_name",
        "Last Name": "last_name",
        "Phone Number": "phone",
        "Gender": "gender",
        "DOB": "date_of_birth",
        "Profile Picture": "profile_image_url",
        "Street": "street_address",
        "City": "city",
        "State": "state",
        "Country": "country",
        "Emergency Contact Name": "emgcy_cont_name",
        "Emergency Contact Relationship": "emgcy_cont_relation",
        "Emergency Contact Phone": "emgcy_cont_num"
    }
    default_fields = [
        "email", "first_name", "last_name", "phone", "gender", "date_of_birth",
        "profile_image_url", "street_address", "city", "state", "country",
        "emgcy_cont_name", "emgcy_cont_relation", "emgcy_cont_num"
    ]

    def get(self, request, *args, **kwargs):

        # Load biz id
        business_id = request.user.profile.business_id

        # Init writer
        csv_writer = csv.writer(
            Echo(),
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL
        )

        # Init response
        response = StreamingHttpResponse(
            self.get_document_set(
                csv_writer=csv_writer,
                business_id=business_id
            ),
            content_type="text/csv"
        )

        # Update response content
        response['Content-Disposition'] = 'attachment; filename="profile.csv"'

        # Start stream
        return response

    def get_document_set(self, **kwargs):
        """Return yield row in csv file."""
        # Load variables
        csv_writer = kwargs.get("csv_writer")
        business_id = kwargs.get("business_id")

        # Convert and yield headers
        headers = self.default_fields
        if self.field_converter:
            headers = list(self.field_converter.keys())
        yield csv_writer.writerow(headers)

        # Loop profile record and yield as rows
        records = Profile.objects.only(*self.default_fields).filter(
            business_id=business_id
        ).iterator()
        for record in records:
            # Load record with only field in defaults
            item = {
                key: record.__dict__[key] for key in self.default_fields
            }

            # Convert field name
            yield_item = {
                field: item.get(key) for field, key in self.field_converter.items()
            }

            # Write row
            yield csv_writer.writerow(yield_item.values())