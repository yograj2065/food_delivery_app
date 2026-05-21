"""
api/utils.py
────────────
Utility functions for the OTP authentication system.

Responsibilities:
  1. generate_otp()        — produce a cryptographically random 6-digit code
  2. send_otp_email()      — send the OTP to the user's email via SMTP
  3. create_otp()          — delete old OTPs and persist a fresh one
  4. get_valid_otp()       — retrieve the latest non-expired, non-verified OTP
"""

import random
import string
import logging

from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 1. OTP Generator
# ─────────────────────────────────────────────

def generate_otp() -> str:
    """
    Generate a cryptographically random 6-digit numeric OTP.
    Uses random.SystemRandom which relies on os.urandom — safe for
    security-sensitive use cases.
    """
    secure_random = random.SystemRandom()
    # Produce exactly 6 digits (zero-padded if needed)
    return ''.join(secure_random.choices(string.digits, k=6))


# ─────────────────────────────────────────────
# 2. Email Sender
# ─────────────────────────────────────────────

def send_otp_email(email: str, otp: str, purpose: str) -> bool:
    """
    Send the OTP to the given email address.

    Args:
        email   : recipient email address
        otp     : 6-digit OTP string
        purpose : 'register' or 'login' — used to customise the subject line

    Returns:
        True on success, False on failure (logs the exception).
    """
    subject_map = {
        'register': 'Your Account Verification Code',
        'login':    'Your Login Verification Code',
    }
    subject = subject_map.get(purpose, 'Your Verification Code')

    message = (
        f"Hello,\n\n"
        f"Your verification code is: {otp}\n\n"
        f"This code expires in 5 minutes.\n"
        f"Do not share this code with anyone.\n\n"
        f"If you did not request this, you can safely ignore this email.\n\n"
        f"Food Ordering System"
    )

    try:
        # Use EmailMessage for full header control — reduces spam scoring
        email_msg = EmailMessage(
            subject=subject,
            body=message,
            from_email=f'Food Ordering System <{settings.EMAIL_HOST_USER}>',
            to=[email],
            reply_to=[settings.EMAIL_HOST_USER],
        )
        email_msg.send(fail_silently=False)
        logger.info(f"OTP email sent to {email} for purpose={purpose}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send OTP email to {email}: {exc}")
        return False


# ─────────────────────────────────────────────
# 3. Create / Refresh OTP
# ─────────────────────────────────────────────

def create_otp(user, purpose: str):
    """
    Delete all previous OTPs for this user+purpose, then create a fresh one.

    This ensures only ONE valid OTP exists at any time per user per purpose,
    preventing replay attacks with stale codes.

    Args:
        user    : Django User instance
        purpose : 'register' or 'login'

    Returns:
        The newly created EmailOTP instance.
    """
    # Import here to avoid circular imports (models → utils → models)
    from .models import EmailOTP

    # Purge all previous OTPs for this user+purpose (expired or not)
    EmailOTP.objects.filter(user=user, purpose=purpose).delete()

    otp_code = generate_otp()

    otp_obj = EmailOTP.objects.create(
        user=user,
        otp=otp_code,
        purpose=purpose,
    )
    return otp_obj


# ─────────────────────────────────────────────
# 4. Retrieve Valid OTP
# ─────────────────────────────────────────────

def get_valid_otp(user, purpose: str, otp_code: str):
    """
    Retrieve the latest OTP for user+purpose and validate it.

    Validation checks (in order):
      1. OTP record exists
      2. Not already verified
      3. Not expired (> 5 minutes old)
      4. Not exceeded max attempts (5)
      5. Code matches

    Args:
        user     : Django User instance
        purpose  : 'register' or 'login'
        otp_code : the code submitted by the user

    Returns:
        (otp_obj, None)          on success
        (None,    error_string)  on failure
    """
    from .models import EmailOTP

    try:
        # Always work with the most recent OTP (ordering = ['-created_at'])
        otp_obj = EmailOTP.objects.filter(
            user=user,
            purpose=purpose,
            is_verified=False,
        ).latest('created_at')
    except EmailOTP.DoesNotExist:
        return None, "No active OTP found. Please request a new one."

    # Check expiry
    if otp_obj.is_expired():
        otp_obj.delete()
        return None, "OTP has expired. Please request a new one."

    # Check attempt limit BEFORE incrementing
    if otp_obj.is_max_attempts():
        otp_obj.delete()
        return None, "Too many failed attempts. Please request a new OTP."

    # Increment attempt counter regardless of match
    otp_obj.attempts += 1
    otp_obj.save(update_fields=['attempts'])

    # Validate the code
    if otp_obj.otp != otp_code:
        remaining = 5 - otp_obj.attempts
        return None, f"Invalid OTP. {remaining} attempt(s) remaining."

    # Mark as verified so it cannot be reused
    otp_obj.is_verified = True
    otp_obj.save(update_fields=['is_verified'])

    return otp_obj, None
