from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("DOCTOR", "Doctor"),
        ("PATIENT", "Patient"),
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="PATIENT"
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
