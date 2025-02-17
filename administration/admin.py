from django.contrib import admin
from django.contrib.auth.models import User

from .models import *

admin.site.register(Locations)
admin.site.register(Rooms)
admin.site.register(Waiver)
admin.site.register(StudioSettings)