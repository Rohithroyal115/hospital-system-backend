from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from .models import TimeSlot, Appointment, AppointmentQueue


# =========================================
# MAIN BOOKING LOGIC (FINAL SAFE VERSION)
# =========================================
@transaction.atomic
def book_appointment(slot_id, patient):

    try:
        slot = TimeSlot.objects.select_for_update().get(id=slot_id)
    except TimeSlot.DoesNotExist:
        raise ValidationError("Slot does not exist")

    # 🔒 Temporary lock check
    if slot.is_locked() and slot.locked_by != patient:
        raise ValidationError("Slot is temporarily locked. Try again.")

    slot.locked_until = timezone.now() + timedelta(seconds=10)
    slot.locked_by = patient
    slot.save()

    # 🔎 Check if slot already booked
    existing_appointment = Appointment.objects.filter(
        slot=slot,
        status="BOOKED"
    ).select_for_update().first()

    # ✅ If slot free → book directly
    if not existing_appointment:
        return _create_appointment(slot, patient)

    # ❗ Slot already booked → add to queue (NO REPLACEMENT)
    _add_to_queue(slot, patient)

    raise ValidationError(
        "Slot already booked. You have been added to waiting queue."
    )


# =========================================
# CREATE APPOINTMENT
# =========================================
def _create_appointment(slot, patient):

    slot.is_booked = True
    slot.locked_until = None
    slot.locked_by = None
    slot.save()

    appointment = Appointment.objects.create(
        doctor=slot.doctor,
        patient=patient,
        slot=slot,
        status="BOOKED",
    )

    return appointment


# =========================================
# ADD TO PRIORITY QUEUE (AGE BASED)
# =========================================
def _add_to_queue(slot, patient):

    already_exists = AppointmentQueue.objects.filter(
        slot=slot,
        patient=patient
    ).exists()

    if not already_exists:
        AppointmentQueue.objects.create(
            slot=slot,
            patient=patient,
            priority_score=patient.get_priority_score()
        )


# =========================================
# PROMOTE FROM QUEUE (CALLED ON CANCEL)
# =========================================
@transaction.atomic
def promote_from_queue(slot):

    next_patient = AppointmentQueue.objects.select_for_update().filter(
        slot=slot
    ).order_by("-priority_score", "requested_at").first()

    if not next_patient:
        slot.is_booked = False
        slot.save()
        return

    AppointmentQueue.objects.filter(
        id=next_patient.id
    ).delete()

    Appointment.objects.create(
        doctor=slot.doctor,
        patient=next_patient.patient,
        slot=slot,
        status="BOOKED",
    )

    slot.is_booked = True
    slot.save()
