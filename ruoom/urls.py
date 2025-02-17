"""ruoom URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.views.generic import RedirectView
from django.views.i18n import JavaScriptCatalog
from django.conf.urls.static import static
from .views import PasswordResetViewRuoom
from . import views
from django.views.generic import RedirectView
from django.contrib import admin
from .forms import DomainPasswordResetForm

app_name = 'admin'

handler400 = 'ruoom.views.handler400'
handler403 = 'ruoom.views.handler403'
handler404 = 'ruoom.views.handler404'
handler500 = 'ruoom.views.handler500'

# Main router
urlpatterns = [
    path('registration/', include('registration.urls')),
    path('administration/', include('administration.urls')),
    path('customer/', include('customer.urls')),
    path('admin/', admin.site.urls),
    path('success/', views.success, name='success'),
    path('unsuccess/', views.unsuccess, name='unsuccess'),
    path('', RedirectView.as_view(url='administration/dashboard/')),
    path('save_studio_picture/', views.SaveStudioPictureView.as_view(), name='save_studio_picture'),
    path('save_profile_picture/', views.SaveProfilePictureView.as_view(), name='save_profile_picture'),
    path(
        'accounts/password_reset/', 
        PasswordResetViewRuoom.as_view(
            html_email_template_name='registration/password_reset_email.html',
            form_class = DomainPasswordResetForm
        ),
        name='password_reset'
    ),
    path('accounts/reset/done/', RedirectView.as_view(pattern_name='administration:dashboard')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
]

# Add media url in development
if settings.DEFAULT_FILE_STORAGE == "django.core.files.storage.FileSystemStorage":
    urlpatterns += static(
        settings.MEDIA_URL, 
        document_root=settings.MEDIA_ROOT
    )

# Add debug toolbar in development
if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
