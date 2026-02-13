from django.contrib import admin
from django import forms
from django.contrib.auth import get_user_model
from .models import Doctor

User = get_user_model()


# =====================================================
# DOCTOR CREATION FORM
# =====================================================
class DoctorCreationForm(forms.ModelForm):
    username = forms.CharField(label="Username")
    email = forms.EmailField(label="Email")
    phone = forms.CharField(label="Phone")
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput
    )

    class Meta:
        model = Doctor
        fields = ["specialization", "available_from", "available_to", "is_available"]

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Phone already exists.")
        return phone


# =====================================================
# DOCTOR ADMIN
# =====================================================
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):

    form = DoctorCreationForm

    list_display = (
        "user",
        "specialization",
        "available_from",
        "available_to",
        "is_available",
    )

    def save_model(self, request, obj, form, change):

        if not change:
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                phone=form.cleaned_data["phone"],
                password=form.cleaned_data["password"],
                role="DOCTOR",
            )
            obj.user = user

        super().save_model(request, obj, form, change)

        # 🔥 Auto-generate slots (no past slots)
        obj.generate_slots_for_today()
