from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from accounts.models import User


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)

    available_from = models.TimeField()
    available_to = models.TimeField()

    # Availability tracking
    is_available = models.BooleanField(default=False)
    last_active_date = models.DateField(null=True, blank=True)

    # =====================================================
    # AUTO SLOT GENERATOR (NO PAST SLOTS)
    # =====================================================
    def generate_slots_for_today(self):
        from appointments.models import TimeSlot  # avoid circular import

        now = timezone.localtime()
        today = now.date()

        start_dt = datetime.combine(today, self.available_from)
        end_dt = datetime.combine(today, self.available_to)

        start_dt = timezone.make_aware(start_dt)
        end_dt = timezone.make_aware(end_dt)

        # If current time passed available_from → start from current rounded time
        if now > start_dt:
            minute_block = (now.minute // 30 + 1) * 30
            rounded = now.replace(minute=0, second=0, microsecond=0)

            if minute_block == 60:
                rounded += timedelta(hours=1)
            else:
                rounded += timedelta(minutes=minute_block)

            start_dt = rounded

        # Generate 30-minute slots
        while start_dt < end_dt:
            TimeSlot.objects.get_or_create(
                doctor=self,
                date=today,
                start_time=start_dt.time()
            )
            start_dt += timedelta(minutes=30)

    # =====================================================
    # AVAILABILITY HELPERS
    # =====================================================
    def mark_available_today(self):
        self.is_available = True
        self.last_active_date = timezone.now().date()
        self.save()

    def mark_unavailable(self):
        self.is_available = False
        self.save()

    @property
    def is_available_today(self):
        return (
            self.is_available
            and self.last_active_date == timezone.now().date()
        )

    def __str__(self):
        return f"{self.user.username} ({self.specialization})"
