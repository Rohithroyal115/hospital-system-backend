from django.contrib import admin
from .models import Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("user", "specialization", "available_from", "available_to", "is_active")
    list_filter = ("specialization", "is_active")
