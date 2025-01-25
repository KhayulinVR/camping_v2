from django.contrib import admin
from service.models import *


# Register your models here.
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'date')
