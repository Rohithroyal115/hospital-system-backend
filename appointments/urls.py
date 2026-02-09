from django.urls import path
from .views import (
    BookAppointmentView,
    MyAppointmentsView,
    CancelAppointmentView,
)

urlpatterns = [
    path("book/", BookAppointmentView.as_view()),
    path("my/", MyAppointmentsView.as_view()),
    path("cancel/<int:appointment_id>/", CancelAppointmentView.as_view()),
]
