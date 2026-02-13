from django.urls import path
from .views import (
    login_view,
    signup_view,
    logout_view,
    patient_dashboard,
    doctor_slots_view,
    forgot_password_view,
    verify_otp_view,
    reset_password_view,
    resend_otp_view,   
)

urlpatterns = [
    # Auth
    path("login/", login_view, name="login"),
    path("signup/", signup_view, name="signup"),
    path("logout/", logout_view, name="logout"),

    # Patient
    path("patient/dashboard/", patient_dashboard, name="patient_dashboard"),
    path("patient/doctor/<int:doctor_id>/slots/", doctor_slots_view, name="doctor_slots"),

    # Forgot Password Flow
    path("forgot-password/", forgot_password_view, name="forgot_password"),
    path("verify-otp/", verify_otp_view, name="verify_otp"),
    path("reset-password/", reset_password_view, name="reset_password"),

    #  NEW ROUTE
    path("resend-otp/", resend_otp_view, name="resend_otp"),
]
