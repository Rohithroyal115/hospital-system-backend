from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random


class User(AbstractUser):

    # =====================================================
    # ROLE SYSTEM
    # =====================================================
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

    # =====================================================
    # PATIENT SYSTEM
    # =====================================================
    PATIENT_TYPE_CHOICES = (
        ("EMERGENCY", "Emergency"),
        ("SENIOR", "Senior Citizen"),
        ("NORMAL", "Normal"),
    )

    patient_type = models.CharField(
        max_length=20,
        choices=PATIENT_TYPE_CHOICES,
        default="NORMAL",
        blank=True
    )

    age = models.PositiveIntegerField(null=True, blank=True)

    # =====================================================
    # CONTACT SYSTEM
    # =====================================================
    email = models.EmailField(unique=True)

    phone = models.CharField(
        max_length=15,
        unique=True
    )

    # =====================================================
    # ANALYTICS SYSTEM
    # =====================================================
    total_appointments = models.IntegerField(default=0)
    total_cancellations = models.IntegerField(default=0)

    last_activity = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=False)

    # =====================================================
    # AUTO CLEAN BASED ON ROLE
    # =====================================================
    def save(self, *args, **kwargs):

        # If Doctor or Admin → remove patient-specific fields
        if self.role in ["DOCTOR", "ADMIN"]:
            self.patient_type = "NORMAL"
            self.age = None

        # If Patient and senior → auto senior classification
        if self.role == "PATIENT" and self.age:
            if self.age >= 60:
                self.patient_type = "SENIOR"

        super().save(*args, **kwargs)

    # =====================================================
    # ACTIVITY TRACKING
    # =====================================================
    def update_activity(self):
        self.last_activity = timezone.now()
        self.is_online = True
        self.save(update_fields=["last_activity", "is_online"])

    def mark_offline(self):
        self.is_online = False
        self.save(update_fields=["is_online"])

    # =====================================================
    # ROLE HELPERS
    # =====================================================
    @property
    def is_patient(self):
        return self.role == "PATIENT"

    @property
    def is_doctor(self):
        return self.role == "DOCTOR"

    @property
    def is_admin_user(self):
        return self.role == "ADMIN"

    # =====================================================
    # ANALYTICS HELPERS
    # =====================================================
    def increment_appointments(self):
        self.total_appointments += 1
        self.save(update_fields=["total_appointments"])

    def increment_cancellations(self):
        self.total_cancellations += 1
        self.save(update_fields=["total_cancellations"])

    def cancellation_rate(self):
        if self.total_appointments == 0:
            return 0
        return round(
            (self.total_cancellations / self.total_appointments) * 100,
            2
        )

    # =====================================================
    # PRIORITY SCORE CALCULATOR
    # =====================================================
    def get_priority_score(self):

        score = 0

        if self.age:
            score += self.age

        if self.patient_type == "EMERGENCY":
            score += 100

        if self.age and self.age >= 60:
            score += 50

        return score

    def __str__(self):
        return f"{self.username} ({self.role})"


# ====================================================
# ENTERPRISE OTP MODEL
# ====================================================
class PasswordResetOTP(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    otp = models.CharField(max_length=6)

    created_at = models.DateTimeField(auto_now_add=True)

    is_verified = models.BooleanField(default=False)

    resend_available_at = models.DateTimeField(null=True, blank=True)

    attempt_count = models.IntegerField(default=0)

    is_locked = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def can_resend(self):
        if not self.resend_available_at:
            return True
        return timezone.now() >= self.resend_available_at

    def increment_attempt(self):
        self.attempt_count += 1
        if self.attempt_count >= 5:
            self.is_locked = True
        self.save(update_fields=["attempt_count", "is_locked"])

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))

    def __str__(self):
        return f"OTP for {self.user.username}"
