from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/appointments/", include("appointments.urls")),
    path("api/doctor/", include("doctors.urls")),
]
