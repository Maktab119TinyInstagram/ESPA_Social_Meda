from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, OTP


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Custom admin for the User model.
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_deleted')
    list_filter = ('is_staff', 'is_active', 'is_deleted')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone', 'bio', 'profile_picture', 'location', 'website')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_deleted', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'updated_at')}),
    )
    
    readonly_fields = ('updated_at',)
    
    actions = ['activate_users', 'deactivate_users', 'soft_delete_users', 'restore_users']
    
    def activate_users(self, request, queryset):
        """
        Activate selected users.
        """
        queryset.update(is_active=True)
        self.message_user(request, _('Selected users have been activated.'))
    activate_users.short_description = _('Activate selected users')
    
    def deactivate_users(self, request, queryset):
        """
        Deactivate selected users.
        """
        queryset.update(is_active=False)
        self.message_user(request, _('Selected users have been deactivated.'))
    deactivate_users.short_description = _('Deactivate selected users')
    
    def soft_delete_users(self, request, queryset):
        """
        Soft delete selected users.
        """
        queryset.update(is_deleted=True)
        self.message_user(request, _('Selected users have been soft deleted.'))
    soft_delete_users.short_description = _('Soft delete selected users')
    
    def restore_users(self, request, queryset):
        """
        Restore soft-deleted users.
        """
        queryset.update(is_deleted=False)
        self.message_user(request, _('Selected users have been restored.'))
    restore_users.short_description = _('Restore selected users')


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    """
    Admin for the OTP model.
    """
    list_display = ('email', 'code', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used',)
    search_fields = ('email',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    actions = ['mark_as_used', 'mark_as_unused']
    
    def mark_as_used(self, request, queryset):
        """
        Mark selected OTPs as used.
        """
        queryset.update(is_used=True)
        self.message_user(request, _('Selected OTPs have been marked as used.'))
    mark_as_used.short_description = _('Mark selected OTPs as used')
    
    def mark_as_unused(self, request, queryset):
        """
        Mark selected OTPs as unused.
        """
        queryset.update(is_used=False)
        self.message_user(request, _('Selected OTPs have been marked as unused.'))
    mark_as_unused.short_description = _('Mark selected OTPs as unused')
