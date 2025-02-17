from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView
from django.template import loader
from django.conf import settings
from django.contrib.auth import login, logout
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect

from registration.forms import CreateCustomerForm, SigninForm, SignupForm
from django.contrib.auth.models import User

from .controller import return_business_id_for_domain
from ruoom.settings import COUNTRY_LANGUAGES
from administration.models import StudioSettings
from registration.models import Profile


def success(request):
    return HttpResponse(_("Successful Signin."))


def unsuccess(request):
    return HttpResponse(_("Unsuccessful Signin."))


def student_signup(request):
	#return HttpResponse("This is where customers sign up for an account.")
    template_name = 'registration/signin.html'
    template = loader.get_template(template_name)
    return HttpResponse(template.render())

def create_account(request):
    if request.method == 'POST':
        form = CreateCustomerForm(request.POST)
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/success/')
    elif request.method == 'GET':
        return HttpResponseRedirect('/unsuccess/')
    else:
        #print(request.method)
        return HttpResponseRedirect('/unsuccess/')

    return render(request, 'registration/signin.html', {'signin_form': form})

class UserSignin(TemplateView):
    template_name = 'registration/sign-in.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        form = SigninForm(request=request)
        self.context = {'signin_form': form}

        business_id = return_business_id_for_domain(request.META.get('HTTP_HOST', ''))
        country_code = StudioSettings.objects.filter(business_id=business_id).first().default_country_code
        self.context['country_code'] = country_code

        redirect_domain = settings.LOGIN_REDIRECT_URL

        # Update context
        self.context.update(
            {
                "redirect_domain": redirect_domain,
                "business_id": business_id
            }
        )

        return render(request, self.template_name, self.context)

    def post(self, request):
        form = SigninForm(request.POST, request=request)
        self.context = {'signin_form': form}
                        
        business_id = return_business_id_for_domain(request.META.get('HTTP_HOST', ''))
        country_code = StudioSettings.objects.filter(business_id=business_id).first().default_country_code
        self.context['country_code'] = country_code
        self.context['business_id'] = business_id

        if form.is_valid():
            user = form.user
            if not user.is_active:
                form.errors['password'] = [_('User is not activated.')]
                return render(request, self.template_name, self.context, status=402)
            login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
            if (request.POST.get("redirect_url",None)):
                response = HttpResponseRedirect(request.POST.get("redirect_url"))
                return response
            elif user.is_customeruser():
                return HttpResponseRedirect(settings.CUSTOMER_LOGIN_REDIRECT_URL)
            else:
                return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
        return render(request, self.template_name, self.context, status=404)

class UserSignup(TemplateView):
    template_name = 'registration/sign-up.html'

    def get(self, request):
        if not hasattr(self, 'context'):
            self.context = {}
        business_id = return_business_id_for_domain(request.META.get('HTTP_HOST', ''))
        redirect_domain = settings.LOGIN_REDIRECT_URL

        form = SignupForm()

        # Update context
        self.context.update(
            {
                "redirect_domain": redirect_domain,
                "business_id": business_id,
                'signup_form': form
            }
        )
        return render(request, self.template_name, self.context)

    def post(self, request):

        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)

        business_id = return_business_id_for_domain(request.META.get('HTTP_HOST', ''))

        form = SignupForm(request.POST)
        self.context = {'signup_form': form}
        self.context['business_id'] = business_id

        if StudioSettings.objects.filter(business_id=business_id):
            country_code = StudioSettings.objects.filter(business_id=business_id).first().default_country_code
            self.context['country_code'] = country_code

        if form.is_valid():
            user = form.save(business_id=business_id)
            self.context['email_message'] = user

            if not user:    #Handle duplicate email errors
                return render(request, self.template_name, self.context)

            user.business_id = business_id
            obj = StudioSettings.objects.filter(business_id=user.business_id).first()
            user.language = COUNTRY_LANGUAGES.get(obj.default_country_code, "en") 

            #If this is the first user in the entire database, go ahead and make it a superuser
            if not User.objects.filter(is_superuser=True).exists():
                user.is_superuser = True
                user.is_staff = True
                user.is_active = True
                user.user_type == Profile.USER_TYPE_STAFF

            user.save()
            login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])

            if not request.COOKIES.get('csrftoken', False) and not user.is_authenticated:     #NEW TAB WORKAROUND FOR IOS SECURITY
                self.context = {'new_tab':True}   
                return self.get(request)
            if (request.POST.get("redirect_url",None)):
                response = HttpResponseRedirect(request.POST.get("redirect_url"))
                return response

            return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            print(form.errors)
            return render(request, self.template_name, self.context)

class CustomerSignIn(TemplateView):
    template_name = 'registration/customer-sign-in.html'

    def get(self, request):
        form = SigninForm(request=request)
        self.context = {'signin_form': form}
                        
        business_id = return_business_id_for_domain(request.META.get('HTTP_HOST', ''))
        country_code = StudioSettings.objects.filter(business_id=business_id).first().default_country_code
        self.context['country_code'] = country_code

        return render(request, self.template_name, self.context)

    def post(self, request):
        form = SigninForm(request.POST, request=request)
        self.context = {'signin_form': form}
                        
        business_id = return_business_id_for_domain(request.META.get('HTTP_HOST', ''))
        country_code = StudioSettings.objects.filter(business_id=business_id).first().default_country_code
        self.context['country_code'] = country_code

        if form.is_valid():
            user = form.user
            if not user.is_active:
                form.errors['password'] = [_('User is not activated.')]
                return render(request, self.template_name, self.context, status=402)
            login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
            if user.is_staffuser():
                return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
            elif user.is_customeruser():
                return HttpResponseRedirect(settings.CUSTOMER_LOGIN_REDIRECT_URL)
            elif user.is_standaloneUser():
                return HttpResponseRedirect(settings.STANDALONE_LOGIN_REDIRECT_URL)
            else:
                return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
        return  render(request, self.template_name, self.context, status=402)

def staff_signout(request):
    if(request.user):
        logout(request)
    return HttpResponseRedirect(settings.LOGIN_URL)

def create_password(request):
    if 'new_password_form' in request.POST:
        if request.POST.get('password') != request.POST.get('password_again'):
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        user = Profile.objects.get(pk=request.user.id)
        user.set_password(request.POST.get('password'))
        user.save()
        login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
