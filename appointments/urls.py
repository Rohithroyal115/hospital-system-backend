from django.urls import path
from .views import (
    BookAppointmentView,
    CancelAppointmentView,
)

urlpatterns = [
    path("book/", BookAppointmentView.as_view(), name="book_appointment"),
    path("cancel/<int:appointment_id>/", CancelAppointmentView.as_view(), name="cancel_appointment"),
]
