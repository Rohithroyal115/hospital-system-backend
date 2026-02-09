from django.db import models
from django.conf import settings


class Doctor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "DOCTOR"}
    )
    specialization = models.CharField(max_length=100)
    available_from = models.TimeField()
    available_to = models.TimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.user.username} - {self.specialization}"
