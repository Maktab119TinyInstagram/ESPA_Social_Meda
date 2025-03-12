import random
import string
from datetime import timedelta

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import OTP


def generate_otp(length=6):
    """
    Generate a random OTP of the specified length.
    """
    return ''.join(random.choices(string.digits, k=length))


def create_otp(email, expiry_minutes=10):
    """
    Create a new OTP for the specified email.
    """
    # Generate a random OTP
    code = generate_otp()
    
    # Calculate the expiry time
    expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
    
    # Create the OTP object
    otp = OTP.objects.create(
        email=email,
        code=code,
        expires_at=expires_at
    )
    
    return otp


def send_otp_email(email, otp_code, is_verification=True):
    """
    Send an OTP email to the specified email address.
    """
    subject = 'Email Verification OTP' if is_verification else 'Login OTP'
    message = f"""
    Your One-Time Password (OTP) for {'email verification' if is_verification else 'login'} is: {otp_code}
    
    This OTP will expire in 10 minutes.
    
    If you did not request this OTP, please ignore this email.
    
    Thank you,
    ESPA Social Network Team
    """
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )


def verify_otp(email, code):
    """
    Verify an OTP for the specified email.
    
    Returns:
        bool: True if the OTP is valid, False otherwise.
    """
    try:
        # Get the latest OTP for the email
        otp = OTP.objects.filter(
            email=email,
            code=code,
            is_used=False,
            expires_at__gt=timezone.now()
        ).latest('created_at')
        
        # Mark the OTP as used
        otp.is_used = True
        otp.save()
        
        return True
    except OTP.DoesNotExist:
        return False 