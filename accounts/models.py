from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    """
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(_('phone number'), max_length=15, blank=True, null=True)
    bio = models.TextField(_('biography'), blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    location = models.CharField(_('location'), max_length=100, blank=True, null=True)
    website = models.URLField(_('website'), blank=True, null=True)
    is_deleted = models.BooleanField(_('deleted'), default=False)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return self.username

    def soft_delete(self):
        """
        Soft delete the user (set is_deleted=True).
        """
        self.is_deleted = True
        self.save()

    def restore(self):
        """
        Restore a soft-deleted user.
        """
        self.is_deleted = False
        self.save()


class OTP(models.Model):
    """
    One-Time Password model for email verification and two-factor authentication.
    """
    email = models.EmailField(_('email address'))
    code = models.CharField(_('verification code'), max_length=6)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'))
    is_used = models.BooleanField(_('used'), default=False)

    class Meta:
        verbose_name = _('OTP')
        verbose_name_plural = _('OTPs')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return f"{self.email} - {self.code}"

    def is_valid(self):
        """
        Check if the OTP is still valid (not expired and not used).
        """
        return not self.is_used and timezone.now() < self.expires_at
