from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    UserProfile, LoginAttempt, SecurityLog, 
    PasswordResetToken, TwoFactorBackupCode, UserSession
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fieldsets = (
        ('Personal Information', {
            'fields': ('bio', 'location', 'birth_date', 'phone_number', 'avatar')
        }),
        ('Social Media', {
            'fields': ('website', 'twitter_handle', 'linkedin_url', 'github_url'),
            'classes': ('collapse',)
        }),
        ('Professional', {
            'fields': ('job_title', 'company'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('email_notifications', 'marketing_emails', 'public_profile', 'two_factor_enabled')
        }),
    )


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'two_factor_status', 'date_joined')
    list_filter = BaseUserAdmin.list_filter + ('profile__two_factor_enabled',)
    
    def two_factor_status(self, obj):
        if hasattr(obj, 'profile') and obj.profile.two_factor_enabled:
            return format_html('<span style="color: green;">✓ Enabled</span>')
        return format_html('<span style="color: red;">✗ Disabled</span>')
    two_factor_status.short_description = "2FA Status"


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_full_name', 'job_title', 'company', 'two_factor_enabled', 'public_profile', 'updated_at')
    list_filter = ('two_factor_enabled', 'public_profile', 'email_notifications', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'bio', 'job_title', 'company')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('public_profile',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('bio', 'location', 'birth_date', 'phone_number', 'avatar')
        }),
        ('Social Media', {
            'fields': ('website', 'twitter_handle', 'linkedin_url', 'github_url'),
            'classes': ('collapse',)
        }),
        ('Professional', {
            'fields': ('job_title', 'company'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('email_notifications', 'marketing_emails', 'public_profile')
        }),
        ('Security', {
            'fields': ('two_factor_enabled', 'backup_tokens_generated'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = "Full Name"


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('username', 'attempt_type_colored', 'ip_address', 'country', 'city', 'created_at')
    list_filter = ('attempt_type', 'country', 'created_at')
    search_fields = ('username', 'ip_address', 'reason')
    readonly_fields = ('created_at',)
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def attempt_type_colored(self, obj):
        colors = {
            'success': 'green',
            'failed': 'red',
            'blocked': 'orange',
            '2fa_failed': 'purple'
        }
        color = colors.get(obj.attempt_type, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_attempt_type_display()
        )
    attempt_type_colored.short_description = "Attempt Type"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type_colored', 'description_short', 'ip_address', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('user__username', 'description', 'ip_address')
    readonly_fields = ('created_at',)
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def event_type_colored(self, obj):
        colors = {
            'login': 'green',
            'logout': 'blue',
            'password_change': 'orange',
            '2fa_enabled': 'green',
            '2fa_disabled': 'red',
            'suspicious_activity': 'red'
        }
        color = colors.get(obj.event_type, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_event_type_display()
        )
    event_type_colored.short_description = "Event Type"
    
    def description_short(self, obj):
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_short.short_description = "Description"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token_short', 'is_used', 'is_expired_display', 'expires_at', 'created_at')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__username', 'user__email', 'token')
    readonly_fields = ('created_at', 'used_at')
    ordering = ['-created_at']
    
    def token_short(self, obj):
        return f"{obj.token[:8]}..."
    token_short.short_description = "Token"
    
    def is_expired_display(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: red;">✗ Expired</span>')
        return format_html('<span style="color: green;">✓ Valid</span>')
    is_expired_display.short_description = "Status"


@admin.register(TwoFactorBackupCode)
class TwoFactorBackupCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code_masked', 'is_used', 'used_at', 'created_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'code')
    readonly_fields = ('created_at', 'used_at', 'used_ip')
    ordering = ['user', '-created_at']
    
    def code_masked(self, obj):
        return f"{obj.code[:4]}****"
    code_masked.short_description = "Code"
    
    def has_add_permission(self, request):
        return False


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type_display', 'ip_address', 'country', 'city', 'is_active', 'last_activity')
    list_filter = ('is_active', 'country', 'last_activity', 'created_at')
    search_fields = ('user__username', 'ip_address', 'user_agent', 'device_info')
    readonly_fields = ('session_key', 'created_at', 'last_activity')
    ordering = ['-last_activity']
    
    def device_type_display(self, obj):
        device_type = obj.get_device_type()
        icons = {
            'Mobile': '📱',
            'Tablet': '📟',
            'Desktop': '💻'
        }
        icon = icons.get(device_type, '❓')
        return f"{icon} {device_type}"
    device_type_display.short_description = "Device"
    
    actions = ['revoke_sessions']
    
    def revoke_sessions(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} sessions revoked.")
    revoke_sessions.short_description = "Revoke selected sessions"