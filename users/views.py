from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from .models import PasswordResetToken
import secrets
import string

class LoginView(auth_views.LoginView):
    template_name = 'users/login.html'

def logout_view(request):
    """Custom logout view that redirects to custom admin login"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('core:admin_login')

class ProfileView(TemplateView):
    template_name = 'users/profile.html'


class ForgotPasswordView(TemplateView):
    template_name = 'users/forgot_password.html'

    def get_admin_user(self):
        admin_user = User.objects.filter(email=settings.EMAIL_HOST_USER, is_staff=True).first()
        if not admin_user:
            admin_user = User.objects.filter(is_superuser=True).first()
        return admin_user

    def post(self, request, *args, **kwargs):
        admin_user = self.get_admin_user()
        if not admin_user:
            messages.error(request, 'Admin account not found. Please contact support.')
            return redirect('core:contact')

        # Generate a secure 6-digit verification code
        digits = string.digits
        code = ''.join(secrets.choice(digits) for _ in range(6))

        # Create token with 15-minute expiry
        PasswordResetToken.objects.create(
            user=admin_user,
            token=code,
            is_used=False,
            ip_address=request.META.get('REMOTE_ADDR', '0.0.0.0'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            expires_at=timezone.now() + timedelta(minutes=15),
        )

        subject = 'Your Habiba admin password reset code'
        plain_message = f"""
You requested a password reset for your admin account.

Your verification code is: {code}

This code expires in 15 minutes. If you did not request this, you can safely ignore this email.

— Habiba Blog Security
"""

        html_message = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color:#2563eb;">Password Reset Verification Code</h2>
  <p>Use the following code to reset your admin password:</p>
  <div style="font-size:28px; font-weight:700; letter-spacing:6px; background:#f3f4f6; padding:16px; text-align:center; border-radius:8px; color:#111827;">{code}</div>
  <p style="margin-top:12px; color:#6b7280;">This code expires in <strong>15 minutes</strong>.</p>
  <hr style="border:none; border-top:1px solid #e5e7eb; margin:20px 0;"/>
  <p style="color:#6b7280; font-size:14px;">If you did not request this, you can ignore this email.</p>
  <p style="color:#6b7280; font-size:12px;">— Habiba Blog Security</p>
  </div>
"""

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],
            html_message=html_message,
            fail_silently=False,
        )

        # Store hint in session for UX and redirect
        request.session['pw_reset_email'] = settings.EMAIL_HOST_USER
        messages.success(request, 'We sent a verification code to your admin email.')
        return redirect('users:verify_code')


class VerifyResetCodeView(TemplateView):
    template_name = 'users/verify_code.html'

    def post(self, request, *args, **kwargs):
        code = request.POST.get('code', '').strip()
        if not code:
            messages.error(request, 'Please enter the verification code.')
            return redirect('users:verify_code')

        admin_user = User.objects.filter(email=settings.EMAIL_HOST_USER, is_staff=True).first()
        if not admin_user:
            admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            messages.error(request, 'Admin account not found. Please contact support.')
            return redirect('core:contact')

        token = PasswordResetToken.objects.filter(user=admin_user, token=code, is_used=False).order_by('-created_at').first()
        if not token:
            messages.error(request, 'Invalid code. Please check and try again.')
            return redirect('users:verify_code')
        if token.is_expired():
            messages.error(request, 'This code has expired. Please request a new one.')
            return redirect('users:forgot_password')

        # Mark verification in session; finalize usage after password reset
        request.session['password_reset_token_id'] = token.id
        messages.success(request, 'Code verified. You can now set a new password.')
        return redirect('users:reset_password')


class ResetPasswordView(TemplateView):
    template_name = 'users/reset_password.html'

    def post(self, request, *args, **kwargs):
        token_id = request.session.get('password_reset_token_id')
        if not token_id:
            messages.error(request, 'Verification required. Please enter your code first.')
            return redirect('users:verify_code')

        try:
            token = PasswordResetToken.objects.get(id=token_id)
        except PasswordResetToken.DoesNotExist:
            messages.error(request, 'Verification token not found. Please try again.')
            return redirect('users:forgot_password')

        if not token.is_valid():
            messages.error(request, 'Your verification has expired. Please request a new code.')
            return redirect('users:forgot_password')

        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not new_password or not confirm_password:
            messages.error(request, 'Please enter and confirm your new password.')
            return redirect('users:reset_password')
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('users:reset_password')

        # Update password using Django's password hasher
        user = token.user
        user.set_password(new_password)
        user.save()

        # Mark token as used and clear session
        token.mark_as_used()
        request.session.pop('password_reset_token_id', None)
        request.session.pop('pw_reset_email', None)

        messages.success(request, 'Your password has been updated. Please log in.')
        return redirect('core:admin_login')