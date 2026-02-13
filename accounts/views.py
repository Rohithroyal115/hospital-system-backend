from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db import transaction
import datetime

from .models import User, PasswordResetOTP
from appointments.models import Appointment, TimeSlot, AppointmentQueue
from doctors.models import Doctor


# ==========================================================
# LOGIN VIEW (FIXED)
# ==========================================================
# ==========================================================
# LOGIN VIEW (FIXED PROPERLY)
# ==========================================================
def login_view(request):

    # If already logged in
    if request.user.is_authenticated:
        if request.user.is_patient:
            return redirect("patient_dashboard")
        elif request.user.is_doctor:
            return redirect("/doctor/dashboard/")
        elif request.user.is_admin_user:
            return redirect("/admin/")

    if request.method == "POST":

        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password"),
        )

        if user:
            login(request, user)
            user.update_activity()

            if user.is_patient:
                return redirect("patient_dashboard")
            elif user.is_doctor:
                return redirect("/doctor/dashboard/")
            elif user.is_admin_user:
                return redirect("/admin/")

        messages.error(request, "Invalid username or password.")

    return render(request, "auth/login.html")


# ==========================================================
# SIGNUP (SAFE AGE PARSE)
# ==========================================================
def signup_view(request):

    if request.user.is_authenticated:
        return redirect("patient_dashboard")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        age = request.POST.get("age")

        if not age:
            messages.error(request, "Age is required.")
            return redirect("signup")

        try:
            age = int(age)
        except ValueError:
            messages.error(request, "Invalid age.")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("signup")

        if User.objects.filter(phone=phone).exists():
            messages.error(request, "Phone already registered.")
            return redirect("signup")

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            phone=phone,
            age=age,
            role="PATIENT",
        )

        login(request, user)
        user.update_activity()

        return redirect("patient_dashboard")

    return render(request, "auth/signup.html")


# ==========================================================
# PATIENT DASHBOARD
# ==========================================================
@login_required
def patient_dashboard(request):

    request.user.update_activity()
    today = timezone.localdate()

    # 🔍 SEARCH FILTER
    search_query = request.GET.get("search")

    available_doctors = Doctor.objects.filter(
        is_available=True,
        last_active_date=today
    )

    if search_query:
        available_doctors = available_doctors.filter(
            specialization__icontains=search_query
        )

    appointments = Appointment.objects.filter(
        patient=request.user
    ).select_related("doctor", "slot")

    queue_entries = AppointmentQueue.objects.filter(
        patient=request.user
    ).select_related("slot", "slot__doctor")

    queue_data = []

    for entry in queue_entries:
        queue_data.append({
            "doctor": entry.slot.doctor,
            "date": entry.slot.date,
            "time": entry.slot.start_time,
            "priority": entry.priority_score,
            "position": entry.get_position()
        })

    return render(request, "patient/dashboard.html", {
        "available_doctors": available_doctors,
        "appointments": appointments,
        "queue_data": queue_data,
        "search_query": search_query
    })

# ==========================================================
# DOCTOR SLOT FILTER
# ==========================================================
@login_required
def doctor_slots_view(request, doctor_id):

    request.user.update_activity()

    now = timezone.localtime()
    today = now.date()
    current_time = now.time()

    slots = TimeSlot.objects.filter(
        doctor_id=doctor_id,
        date__gte=today,
        is_booked=False
    ).order_by("date", "start_time")

    valid_slots = []

    for slot in slots:
        if slot.date > today:
            valid_slots.append(slot)
        elif slot.date == today and slot.start_time > current_time:
            valid_slots.append(slot)

    return render(request, "patient/slots.html", {
        "slots": valid_slots
    })


# ==========================================================
# JOIN QUEUE
# ==========================================================
@login_required
@transaction.atomic
def join_queue(request, slot_id):

    slot = get_object_or_404(TimeSlot, id=slot_id)
    now = timezone.localtime()

    if slot.date == now.date() and slot.start_time <= now.time():
        messages.error(request, "This slot has already passed.")
        return redirect("patient_dashboard")

    AppointmentQueue.objects.create(
        slot=slot,
        patient=request.user,
        priority_score=request.user.get_priority_score()
    )

    messages.success(request, "Added to queue successfully.")
    return redirect("patient_dashboard")


# ==========================================================
# FORGOT PASSWORD (OTP EMAIL)
# ==========================================================
def forgot_password_view(request):

    if request.method == "POST":

        identifier = request.POST.get("identifier")

        try:
            if "@" in identifier:
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(phone=identifier)
        except User.DoesNotExist:
            messages.error(request, "No account found.")
            return redirect("forgot_password")

        otp_code = PasswordResetOTP.generate_otp()

        PasswordResetOTP.objects.create(
            user=user,
            otp=otp_code,
            resend_available_at=timezone.now() + datetime.timedelta(seconds=60)
        )

        email = EmailMultiAlternatives(
            "MediCare+ Password Reset OTP",
            f"Your OTP is {otp_code}. Valid for 5 minutes.",
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )

        email.send()

        request.session["reset_user_id"] = user.id
        request.session["otp_verified"] = False

        messages.success(request, "OTP sent to your email.")
        return redirect("verify_otp")

    return render(request, "auth/forgot_password.html")


# ==========================================================
# VERIFY OTP
# ==========================================================
def verify_otp_view(request):

    user_id = request.session.get("reset_user_id")

    if not user_id:
        return redirect("forgot_password")

    if request.method == "POST":

        entered_otp = request.POST.get("otp")

        otp_entry = PasswordResetOTP.objects.filter(
            user_id=user_id,
            otp=entered_otp,
            is_verified=False,
            is_locked=False
        ).order_by("-created_at").first()

        if not otp_entry:
            messages.error(request, "Invalid OTP.")
            return redirect("verify_otp")

        if otp_entry.is_expired():
            messages.error(request, "OTP expired.")
            return redirect("forgot_password")

        otp_entry.is_verified = True
        otp_entry.save()

        request.session["otp_verified"] = True
        return redirect("reset_password")

    return render(request, "auth/verify_otp.html")


# ==========================================================
# RESET PASSWORD
# ==========================================================
def reset_password_view(request):

    user_id = request.session.get("reset_user_id")

    if not user_id or not request.session.get("otp_verified"):
        return redirect("forgot_password")

    if request.method == "POST":

        new_password = request.POST.get("password")

        user = User.objects.get(id=user_id)
        user.password = make_password(new_password)
        user.save()

        PasswordResetOTP.objects.filter(user=user).delete()
        request.session.flush()

        messages.success(request, "Password reset successful.")
        return redirect("login")

    return render(request, "auth/reset_password.html")


# ==========================================================
# LOGOUT
# ==========================================================
def logout_view(request):

    if request.user.is_authenticated:
        request.user.mark_offline()

    logout(request)
    return redirect("/")
def resend_otp_view(request):

    user_id = request.session.get("reset_user_id")

    if not user_id:
        return redirect("forgot_password")

    user = User.objects.get(id=user_id)

    otp_code = PasswordResetOTP.generate_otp()

    PasswordResetOTP.objects.create(
        user=user,
        otp=otp_code,
        resend_available_at=timezone.now() + datetime.timedelta(seconds=60)
    )

    email = EmailMultiAlternatives(
        "Resent OTP",
        f"Your new OTP is {otp_code}",
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    email.send()

    messages.success(request, "New OTP sent.")
    return redirect("verify_otp")