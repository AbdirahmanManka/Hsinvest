from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import RegexValidator
from PIL import Image
import os


class UserProfile(models.Model):
    """Extended user profile information"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Profile Information
    bio = models.TextField(max_length=500, blank=True, help_text="Short bio about yourself")
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    phone_number = models.CharField(
        max_length=15, 
        blank=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    
    # Profile Image
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        help_text="Profile picture"
    )
    
    # Social Media Links
    website = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True, help_text="Without @ symbol")
    linkedin_url = models.URLField(blank=True)
    
    # Professional Information
    job_title = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=100, blank=True)
    
    # Settings
    email_notifications = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)
    public_profile = models.BooleanField(default=True, help_text="Make profile visible to others")
    
    # 2FA Settings
    two_factor_enabled = models.BooleanField(default=False)
    backup_tokens_generated = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Resize avatar if it exists
        if self.avatar:
            self.resize_avatar()
    
    def resize_avatar(self):
        """Resize avatar to reasonable size"""
        try:
            img = Image.open(self.avatar.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size, Image.LANCZOS)
                img.save(self.avatar.path)
        except Exception as e:
            pass  # Handle silently if PIL fails
    
    def get_full_name(self):
        """Get user's full name or username if name not available"""
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username
    
    def get_display_name(self):
        """Get name to display publicly"""
        if self.user.first_name:
            return self.user.first_name
        return self.user.username


class LoginAttempt(models.Model):
    """Track login attempts for security"""
    
    ATTEMPT_TYPES = [
        ('success', 'Successful Login'),
        ('failed', 'Failed Login'),
        ('blocked', 'Blocked Attempt'),
        ('2fa_failed', '2FA Failed'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='login_attempts'
    )
    username = models.CharField(max_length=150)
    attempt_type = models.CharField(max_length=20, choices=ATTEMPT_TYPES)
    
    # Technical Information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Location (can be populated by GeoIP or external service)
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Additional Info
    reason = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Login Attempt"
        verbose_name_plural = "Login Attempts"
        indexes = [
            models.Index(fields=['username', 'created_at']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        return f"{self.username} - {self.get_attempt_type_display()} ({self.created_at})"


class SecurityLog(models.Model):
    """Log security-related events"""
    
    EVENT_TYPES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('password_change', 'Password Changed'),
        ('2fa_enabled', '2FA Enabled'),
        ('2fa_disabled', '2FA Disabled'),
        ('2fa_backup_used', '2FA Backup Code Used'),
        ('profile_updated', 'Profile Updated'),
        ('suspicious_activity', 'Suspicious Activity'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_logs')
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    description = models.TextField()
    
    # Technical Information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Additional Data (JSON field would be better but keeping it simple)
    additional_data = models.TextField(blank=True, help_text="JSON data for additional context")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Security Log"
        verbose_name_plural = "Security Logs"
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_event_type_display()}"


class PasswordResetToken(models.Model):
    """Custom password reset tokens with expiration"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    
    # Security
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Expiration
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Password Reset Token"
        verbose_name_plural = "Password Reset Tokens"
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_used']),
        ]
    
    def __str__(self):
        return f"Reset token for {self.user.username}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.is_used and not self.is_expired()
    
    def mark_as_used(self):
        self.is_used = True
        self.used_at = timezone.now()
        self.save()


class TwoFactorBackupCode(models.Model):
    """Backup codes for 2FA recovery"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='backup_codes')
    code = models.CharField(max_length=20, unique=True)
    
    # Usage tracking
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    used_ip = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "2FA Backup Code"
        verbose_name_plural = "2FA Backup Codes"
        unique_together = ['user', 'code']
    
    def __str__(self):
        status = "Used" if self.is_used else "Active"
        return f"{self.user.username} - {self.code[:4]}**** ({status})"
    
    def mark_as_used(self, ip_address=None):
        self.is_used = True
        self.used_at = timezone.now()
        if ip_address:
            self.used_ip = ip_address
        self.save()


class UserSession(models.Model):
    """Track active user sessions"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_sessions')
    session_key = models.CharField(max_length=40, unique=True)
    
    # Session Information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_info = models.CharField(max_length=200, blank=True)
    
    # Location
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "User Session"
        verbose_name_plural = "User Sessions"
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.username} - {self.device_info or 'Unknown Device'}"
    
    def is_current_session(self, request):
        return request.session.session_key == self.session_key
    
    def get_device_type(self):
        """Simple device detection from user agent"""
        ua_lower = self.user_agent.lower()
        if 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
            return 'Mobile'
        elif 'tablet' in ua_lower or 'ipad' in ua_lower:
            return 'Tablet'
        else:
            return 'Desktop'


# Signal handlers to create user profile automatically
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()