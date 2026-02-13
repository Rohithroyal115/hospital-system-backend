from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import Doctor
from appointments.models import Appointment


# ======================
# DOCTOR LOGIN
# ======================
def doctor_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user and user.role == "DOCTOR":
            login(request, user)

            doctor = Doctor.objects.get(user=user)

            doctor.is_available = True
            doctor.last_active_date = timezone.now().date()
            doctor.save()

            # ✅ AUTO GENERATE SLOTS (MODEL METHOD)
            doctor.generate_slots_for_today()

            return redirect("/doctor/dashboard/")
        else:
            messages.error(request, "Invalid doctor credentials")

    return render(request, "doctor/login.html")


# ======================
# DOCTOR DASHBOARD
# ======================
@login_required
def doctor_dashboard(request):
    doctor = Doctor.objects.get(user=request.user)

    appointments = Appointment.objects.filter(
        doctor=doctor,
        status="BOOKED"
    ).select_related("patient", "slot")

    return render(
        request,
        "doctor/dashboard.html",
        {
            "appointments": appointments,
            "doctor": doctor
        }
    )


# ======================
# TOGGLE AVAILABILITY
# ======================
@login_required
def toggle_availability(request):
    if request.method == "POST":
        doctor = Doctor.objects.get(user=request.user)

        doctor.is_available = not doctor.is_available

        if doctor.is_available:
            doctor.last_active_date = timezone.now().date()

        doctor.save()

    return redirect("doctor_dashboard")


# ======================
# MARK COMPLETE
# ======================
@login_required
def complete_appointment(request, appointment_id):
    appointment = Appointment.objects.get(
        id=appointment_id,
        doctor__user=request.user
    )
    appointment.status = "COMPLETED"
    appointment.save()

    return redirect("/doctor/dashboard/")


# ======================
# DOCTOR LOGOUT
# ======================
@login_required
def doctor_logout_view(request):
    doctor = Doctor.objects.get(user=request.user)
    doctor.is_available = False
    doctor.save()

    logout(request)
    return redirect("/doctor/login/")
