from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.permissions import IsDoctor
from .models import Doctor
from .serializers import DoctorSlotSerializer, DoctorAppointmentSerializer
from appointments.models import TimeSlot, Appointment
class DoctorSlotsView(APIView):
    permission_classes = [IsDoctor]

    def get(self, request):
        doctor = Doctor.objects.get(user=request.user)
        slots = TimeSlot.objects.filter(doctor=doctor)
        serializer = DoctorSlotSerializer(slots, many=True)
        return Response(serializer.data)
class DoctorAppointmentsView(APIView):
    permission_classes = [IsDoctor]

    def get(self, request):
        doctor = Doctor.objects.get(user=request.user)
        appointments = Appointment.objects.filter(doctor=doctor)
        serializer = DoctorAppointmentSerializer(appointments, many=True)
        return Response(serializer.data)
class CompleteAppointmentView(APIView):
    permission_classes = [IsDoctor]

    def post(self, request, appointment_id):
        doctor = Doctor.objects.get(user=request.user)

        try:
            appointment = Appointment.objects.get(
                id=appointment_id,
                doctor=doctor
            )
        except Appointment.DoesNotExist:
            return Response(
                {"error": "Appointment not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        appointment.status = "COMPLETED"
        appointment.save()

        return Response({"message": "Appointment marked as completed"})
