from datetime import datetime, timedelta
from django.db import transaction
from django.core.exceptions import ValidationError

from doctors.models import Doctor
from .models import TimeSlot, Appointment


@transaction.atomic
def book_appointment(slot_id, patient):
    try:
        slot = TimeSlot.objects.select_for_update().get(id=slot_id)
    except TimeSlot.DoesNotExist:
        raise ValidationError("Slot does not exist")

    if slot.is_booked:
        raise ValidationError("Slot already booked")

    slot.is_booked = True
    slot.save()

    appointment = Appointment.objects.create(
        doctor=slot.doctor,
        patient=patient,
        slot=slot,
        status="BOOKED"
    )

    return appointment


@transaction.atomic
def generate_slots_for_doctor(doctor_id, date, slot_minutes=30):
    doctor = Doctor.objects.select_for_update().get(id=doctor_id)

    start_time = datetime.combine(date, doctor.available_from)
    end_time = datetime.combine(date, doctor.available_to)

    current_time = start_time
    slots_created = []

    while current_time + timedelta(minutes=slot_minutes) <= end_time:
        slot, created = TimeSlot.objects.get_or_create(
            doctor=doctor,
            date=date,
            start_time=current_time.time(),
            defaults={"is_booked": False},
        )

        if created:
            slots_created.append(slot)

        current_time += timedelta(minutes=slot_minutes)

    return slots_created
