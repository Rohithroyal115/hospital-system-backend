from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError

from .models import Appointment
from .serializers import AppointmentSerializer
from .services import book_appointment
from accounts.permissions import IsPatient


class BookAppointmentView(APIView):
    permission_classes = [IsPatient]

    def post(self, request):
        slot_id = request.data.get("slot_id")

        if not slot_id:
            return Response(
                {"error": "slot_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            appointment = book_appointment(slot_id, request.user)
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MyAppointmentsView(APIView):
    permission_classes = [IsPatient]

    def get(self, request):
        appointments = Appointment.objects.filter(patient=request.user)
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)


class CancelAppointmentView(APIView):
    permission_classes = [IsPatient]

    def post(self, request, appointment_id):
        try:
            appointment = Appointment.objects.get(
                id=appointment_id,
                patient=request.user
            )
        except Appointment.DoesNotExist:
            return Response(
                {"error": "Appointment not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        appointment.status = "CANCELLED"
        appointment.slot.is_booked = False
        appointment.slot.save()
        appointment.save()

        return Response({"message": "Appointment cancelled"})
