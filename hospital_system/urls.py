from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render


def home_view(request):
    return render(request, "home.html")


urlpatterns = [
    # Home page
    path("", home_view, name="home"),

    # Accounts (login, signup, patient pages)
    path("", include("accounts.urls")),

    # Doctor pages
    path("doctor/", include("doctors.urls")),

    # APIs
    path("api/appointments/", include("appointments.urls")),
    path("api/doctor/", include("doctors.urls")),

    # Admin
    path("admin/", admin.site.urls),
]
