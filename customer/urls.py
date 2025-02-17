from django.urls import path
from .views import *
from django.views.decorators.csrf import csrf_exempt

app_name = 'customer'
urlpatterns = [
    path('', (CustomerAccount.as_view()), name='customer-default'),
    path('account-settings/', CustomerAccountSettings.as_view(), name='customer-account-settings'),
    path('ajax/get_profile_results/', ajax_for_get_profile_results, name='get_profile_results'),
]
