from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings as django_settings
from doctors.models import Doctor


# ==========================================================
# TIME SLOT MODEL
# ==========================================================
class TimeSlot(models.Model):

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="slots"
    )

    date = models.DateField()
    start_time = models.TimeField()

    is_booked = models.BooleanField(default=False)

    locked_until = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="locked_slots"
    )

    class Meta:
        unique_together = ("doctor", "date", "start_time")
        ordering = ["date", "start_time"]
        indexes = [
            models.Index(fields=["doctor", "date"]),
        ]

    def is_locked(self):
        return self.locked_until and self.locked_until > timezone.now()

    def __str__(self):
        return f"{self.doctor} | {self.date} {self.start_time}"


# ==========================================================
# MAIN APPOINTMENT MODEL
# ==========================================================
class Appointment(models.Model):

    STATUS_CHOICES = (
        ("BOOKED", "Booked"),
        ("CANCELLED", "Cancelled"),
        ("COMPLETED", "Completed"),
    )

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "PATIENT"}
    )

    # Keep OneToOne (Correct Design)
    slot = models.OneToOneField(TimeSlot, on_delete=models.CASCADE)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="BOOKED"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["doctor", "status"]),
        ]

    def __str__(self):
        return f"Appointment #{self.id} | {self.patient} -> {self.doctor}"

    # ======================================================
    # PROMOTE NEXT PATIENT FROM QUEUE
    # ======================================================
    @transaction.atomic
    def promote_next_patient(self):

        next_entry = AppointmentQueue.objects.select_for_update().filter(
            slot=self.slot
        ).order_by("-priority_score", "requested_at").first()

        if not next_entry:
            # No queue → free slot
            self.slot.is_booked = False
            self.slot.save()
            return

        # Create new appointment for next patient
        Appointment.objects.create(
            doctor=self.doctor,
            patient=next_entry.patient,
            slot=self.slot,
            status="BOOKED"
        )

        # Update analytics
        next_entry.patient.total_appointments += 1
        next_entry.patient.save(update_fields=["total_appointments"])

        # Remove from queue
        next_entry.delete()

        # Notify patient
        send_mail(
            subject="MediCare+ Appointment Confirmed",
            message=f"""
Dear {next_entry.patient.username},

You have been auto-booked for:

Doctor: {self.doctor.user.username}
Date: {self.slot.date}
Time: {self.slot.start_time}

Please login to view details.

Regards,
MediCare+
""",
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[next_entry.patient.email],
        )

    # ======================================================
    # SAVE OVERRIDE (FIXED)
    # ======================================================
    def save(self, *args, **kwargs):

        is_new = self.pk is None

        # 🔥 Handle cancellation safely
        if not is_new:
            old_status = Appointment.objects.get(pk=self.pk).status

            if old_status == "BOOKED" and self.status == "CANCELLED":

                # Increase cancellation count
                self.patient.total_cancellations += 1
                self.patient.save(update_fields=["total_cancellations"])

                # Promote next patient OR free slot
                self.promote_next_patient()

                # 🔥 DELETE this appointment (prevents OneToOne conflict)
                super().delete()
                return

        super().save(*args, **kwargs)

        # 🔥 Handle new booking
        if is_new:
            self.slot.is_booked = True
            self.slot.save()

            self.patient.total_appointments += 1
            self.patient.save(update_fields=["total_appointments"])


# ==========================================================
# PRIORITY QUEUE MODEL
# ==========================================================
class AppointmentQueue(models.Model):

    slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name="waiting_queue"
    )

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    priority_score = models.IntegerField()
    admin_override = models.BooleanField(default=False)
    requested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-priority_score", "requested_at"]
        unique_together = ("slot", "patient")

    def __str__(self):
        return f"Queue | {self.patient} (Priority {self.priority_score})"

    def calculate_priority(self):
        score = 0

        if self.patient.age:
            score += self.patient.age

        if getattr(self.patient, "patient_type", None) == "EMERGENCY":
            score += 100

        if self.patient.age and self.patient.age >= 60:
            score += 50

        return score

    def save(self, *args, **kwargs):
        if not self.admin_override:
            self.priority_score = self.calculate_priority()

        super().save(*args, **kwargs)

    def get_position(self):
        higher = AppointmentQueue.objects.filter(
            slot=self.slot,
            priority_score__gt=self.priority_score
        ).count()

        return higher + 1
