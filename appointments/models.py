from django.db import models
from django.conf import settings
from doctors.models import Doctor


class TimeSlot(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="slots")
    date = models.DateField()
    start_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        unique_together = ("doctor", "date", "start_time")
        ordering = ["date", "start_time"]

    def __str__(self):
        return f"{self.doctor} | {self.date} {self.start_time}"
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
    slot = models.OneToOneField(TimeSlot, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="BOOKED")
    
