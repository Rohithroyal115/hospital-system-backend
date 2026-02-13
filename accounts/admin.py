from django.contrib import admin
from .models import User, PasswordResetOTP


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "phone", "role")
    search_fields = ("username", "email", "phone")
    list_filter = ("role",)


@admin.register(PasswordResetOTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("user", "otp", "created_at", "is_verified")
