from rest_framework.views import APIView
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Appointment
from .services import book_appointment, promote_from_queue
from accounts.permissions import IsPatient


# ======================================
# BOOK APPOINTMENT
# ======================================
class BookAppointmentView(APIView):
    permission_classes = [IsPatient]

    def post(self, request):
        slot_id = request.data.get("slot_id") or request.POST.get("slot_id")

        if not slot_id:
            messages.error(request, "Invalid slot.")
            return redirect("/patient/dashboard/")

        try:
            book_appointment(slot_id, request.user)
            messages.success(request, "Appointment booked successfully!")
        except ValidationError as e:
            messages.error(request, str(e))

        return redirect("/patient/dashboard/")


# ======================================
# CANCEL APPOINTMENT
# ======================================
class CancelAppointmentView(APIView):
    permission_classes = [IsPatient]

    @transaction.atomic
    def post(self, request, appointment_id):

        try:
            appointment = Appointment.objects.select_for_update().get(
                id=appointment_id,
                patient=request.user
            )
        except Appointment.DoesNotExist:
            messages.error(request, "Appointment not found.")
            return redirect("/patient/dashboard/")

        slot = appointment.slot

        # Cancel current appointment
        appointment.status = "CANCELLED"
        appointment.save()

        # Promote next patient from queue (if any)
        promote_from_queue(slot)

        messages.success(request, "Appointment cancelled.")

        return redirect("/patient/dashboard/")
