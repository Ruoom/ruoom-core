from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'administration'
urlpatterns = [
    path('', RedirectView.as_view(url='dashboard/')),
    path('dashboard/', views.Dashboard.as_view(), name='dashboard'),
    path('customers/', views.CustomerPage.as_view(), name='customers'),
    path('customers/modify/option', views.CustomerOptions.as_view(), name='customers_nav_bar'),
    path('schedule/', views.Schedule.as_view(), name='schedule'),
    path('staff/', views.StaffPage.as_view(), name='staff'),
    path('locations/', views.Locations.as_view(), name='locations'),
    path('permissions/', views.Admin.as_view(), name='admin'),
    path('settings/', views.Settings.as_view(), name='settings'),
    path('settings/embed/', views.settingsEmbed, name='settings-embed'),
    path('settings/contact/', views.settingsContact, name='settings-contact'),
    
    path('customers/search/', views.CustomersSearch.as_view(), name='customersearch'),
    path('profile/search/', views.ProfileSearch.as_view(), name='profilesearch'),
    path('staff/search/', views.StaffSearch.as_view(), name='staff_search'),
    path("ajax/room/select", views.ajax_for_selected_room_on_modal, name="ajax_for_selected_room_on_modal"),
    path("location/upload/waiver/", views.UploadWaiverView.as_view(), name="location_upload_waiver"),

    path('help/', views.Help.as_view(), name='help'),
    path('help/embed/', views.HelpEmbed.as_view(), name='helpEmbed'),
    path('help/email/', views.HelpEmail.as_view(), name='helpEmail'),
    
    path('staff/list/', views.StaffPage.as_view(), name='staff-list'),

    path('langselect/', (views.LanguageSelect.as_view()), name='language-select'),
    path('media/<str:path>', views.download_media, name='download_media'),
    path('export_profile', views.ExportProfile.as_view(), name='export_profile'),
    path('nolocation', views.no_location, name='no_location'),
]
