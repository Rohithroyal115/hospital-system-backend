from django.urls import path
from .views import (
    doctor_login_view,
    doctor_dashboard,
    doctor_logout_view,
    complete_appointment,
    toggle_availability,
)

urlpatterns = [
    path("login/", doctor_login_view, name="doctor_login"),
    path("dashboard/", doctor_dashboard, name="doctor_dashboard"),
    path("logout/", doctor_logout_view, name="doctor_logout"),
    path("complete/<int:appointment_id>/", complete_appointment, name="complete_appointment"),
    path("toggle-availability/", toggle_availability, name="toggle_availability"),
]
