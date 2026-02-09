from rest_framework import serializers
from appointments.models import TimeSlot, Appointment


class DoctorSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ["id", "date", "start_time", "is_booked"]


class DoctorAppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.username", read_only=True)

    class Meta:
        model = Appointment
        fields = ["id", "patient_name", "slot", "status"]
