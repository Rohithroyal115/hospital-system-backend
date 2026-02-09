
from django.urls import path
from .views import (
    DoctorSlotsView,
    DoctorAppointmentsView,
    CompleteAppointmentView,
)

urlpatterns = [
    path("slots/", DoctorSlotsView.as_view()),
    path("appointments/", DoctorAppointmentsView.as_view()),
    path("appointments/<int:appointment_id>/complete/", CompleteAppointmentView.as_view()),
]
