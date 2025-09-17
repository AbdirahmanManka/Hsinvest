from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import EmailValidator
from django.urls import reverse
from ckeditor_uploader.fields import RichTextUploadingField
from blog.models import BlogPost, Category
import uuid
from datetime import timedelta


class NewsletterSubscriber(models.Model):
    """Newsletter email subscribers"""
    
    SUBSCRIPTION_STATUS = [
        ('active', 'Active'),
        ('unsubscribed', 'Unsubscribed'),
        ('bounced', 'Bounced'),
        ('spam_complaint', 'Spam Complaint'),
    ]
    
    # Basic Information
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    
    # Subscription Details
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='active')
    subscription_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Preferences
    subscription_interests = models.ManyToManyField(
        Category, 
        blank=True,
        help_text="Categories they're interested in"
    )
    frequency_preference = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('immediately', 'Immediate (New Posts)'),
        ],
        default='weekly'
    )
    
    # Technical Information
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    referrer_url = models.URLField(blank=True, help_text="Where they subscribed from")
    
    # Geographic Information
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Engagement Metrics
    total_emails_sent = models.PositiveIntegerField(default=0)
    total_emails_opened = models.PositiveIntegerField(default=0)
    total_links_clicked = models.PositiveIntegerField(default=0)
    last_engagement = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Email verification
    is_verified = models.BooleanField(default=False)
    verification_sent_at = models.DateTimeField(blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"
        ordering = ['-subscribed_at']
    
    def __str__(self):
        name = self.get_full_name()
        return f"{name} ({self.email}) - {self.get_status_display()}"
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.email.split('@')[0]
    
    def get_unsubscribe_url(self):
        return reverse('newsletter:unsubscribe', kwargs={'token': self.subscription_token})
    
    def get_engagement_rate(self):
        if self.total_emails_sent > 0:
            return round((self.total_emails_opened / self.total_emails_sent) * 100, 1)
        return 0
    
    def is_engaged(self):
        """Check if subscriber is engaged (opened email in last 30 days)"""
        if self.last_engagement:
            return timezone.now() - self.last_engagement <= timedelta(days=30)
        return False
    
    def unsubscribe(self, reason="user_request"):
        self.status = 'unsubscribed'
        self.unsubscribed_at = timezone.now()
        self.save()
        
        # Log the unsubscription
        NewsletterActivity.objects.create(
            subscriber=self,
            activity_type='unsubscription',
            description=f"Unsubscribed: {reason}"
        )


class EmailCampaign(models.Model):
    """Email campaigns and newsletters"""
    
    CAMPAIGN_STATUS = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    CAMPAIGN_TYPES = [
        ('newsletter', 'Newsletter'),
        ('announcement', 'Announcement'),
        ('blog_digest', 'Blog Digest'),
        ('welcome', 'Welcome Email'),
        ('promotional', 'Promotional'),
    ]
    
    # Campaign Details
    name = models.CharField(max_length=200, help_text="Internal campaign name")
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPES, default='newsletter')
    subject = models.CharField(max_length=200, help_text="Email subject line")
    preheader = models.CharField(max_length=150, blank=True, help_text="Preview text")
    
    # Content
    content = RichTextUploadingField(help_text="Email content")
    plain_text_content = models.TextField(blank=True, help_text="Plain text version")
    
    # Sender Information
    from_name = models.CharField(max_length=100, default="Habiba's Blog")
    from_email = models.EmailField()
    reply_to_email = models.EmailField(blank=True)
    
    # Targeting
    send_to_all = models.BooleanField(default=True, help_text="Send to all active subscribers")
    target_categories = models.ManyToManyField(
        Category, 
        blank=True,
        help_text="Send only to subscribers interested in these categories"
    )
    target_subscribers = models.ManyToManyField(
        NewsletterSubscriber,
        blank=True,
        help_text="Specific subscribers to target"
    )
    
    # Scheduling
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS, default='draft')
    scheduled_at = models.DateTimeField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    
    # Analytics
    total_recipients = models.PositiveIntegerField(default=0)
    total_sent = models.PositiveIntegerField(default=0)
    total_delivered = models.PositiveIntegerField(default=0)
    total_bounced = models.PositiveIntegerField(default=0)
    total_opened = models.PositiveIntegerField(default=0)
    total_clicked = models.PositiveIntegerField(default=0)
    total_unsubscribed = models.PositiveIntegerField(default=0)
    total_spam_complaints = models.PositiveIntegerField(default=0)
    
    # Related Content
    featured_posts = models.ManyToManyField(
        BlogPost,
        blank=True,
        help_text="Blog posts to feature in this campaign"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Email Campaign"
        verbose_name_plural = "Email Campaigns"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def get_open_rate(self):
        if self.total_sent > 0:
            return round((self.total_opened / self.total_sent) * 100, 1)
        return 0
    
    def get_click_rate(self):
        if self.total_sent > 0:
            return round((self.total_clicked / self.total_sent) * 100, 1)
        return 0
    
    def get_unsubscribe_rate(self):
        if self.total_sent > 0:
            return round((self.total_unsubscribed / self.total_sent) * 100, 1)
        return 0
    
    def get_delivery_rate(self):
        if self.total_recipients > 0:
            return round((self.total_delivered / self.total_recipients) * 100, 1)
        return 0


class EmailTemplate(models.Model):
    """Reusable email templates"""
    
    TEMPLATE_TYPES = [
        ('newsletter', 'Newsletter'),
        ('welcome', 'Welcome Email'),
        ('blog_notification', 'New Blog Post'),
        ('digest', 'Blog Digest'),
        ('announcement', 'Announcement'),
        ('custom', 'Custom Template'),
    ]
    
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPES, default='custom')
    description = models.TextField(blank=True)
    
    # Template Content
    subject_template = models.CharField(max_length=200, help_text="Use {{variable}} for dynamic content")
    html_content = RichTextUploadingField()
    plain_text_content = models.TextField(blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text="Default template for this type")
    
    # Usage Stats
    times_used = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Email Template"
        verbose_name_plural = "Email Templates"
        ordering = ['template_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class NewsletterActivity(models.Model):
    """Track newsletter-related activities"""
    
    ACTIVITY_TYPES = [
        ('subscription', 'New Subscription'),
        ('unsubscription', 'Unsubscription'),
        ('email_sent', 'Email Sent'),
        ('email_opened', 'Email Opened'),
        ('link_clicked', 'Link Clicked'),
        ('bounce', 'Email Bounced'),
        ('spam_complaint', 'Spam Complaint'),
        ('verification_sent', 'Verification Email Sent'),
        ('email_verified', 'Email Verified'),
    ]
    
    subscriber = models.ForeignKey(
        NewsletterSubscriber, 
        on_delete=models.CASCADE,
        related_name='activities'
    )
    campaign = models.ForeignKey(
        EmailCampaign,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='activities'
    )
    
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.TextField(blank=True)
    
    # Additional Data
    email_subject = models.CharField(max_length=200, blank=True)
    clicked_url = models.URLField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Newsletter Activity"
        verbose_name_plural = "Newsletter Activities"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['activity_type', 'created_at']),
            models.Index(fields=['subscriber', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.subscriber.email} - {self.get_activity_type_display()}"


class AutomatedEmail(models.Model):
    """Automated email sequences (welcome series, etc.)"""
    
    TRIGGER_TYPES = [
        ('subscription', 'New Subscription'),
        ('blog_post', 'New Blog Post'),
        ('category_post', 'New Post in Category'),
        ('schedule', 'Scheduled Send'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)
    
    # Email Content
    email_template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.CASCADE,
        related_name='automated_emails'
    )
    
    # Trigger Settings
    delay_hours = models.PositiveIntegerField(
        default=0,
        help_text="Hours to wait before sending (0 for immediate)"
    )
    trigger_category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="For category-specific triggers"
    )
    
    # Settings
    is_active = models.BooleanField(default=True)
    max_sends_per_subscriber = models.PositiveIntegerField(
        default=1,
        help_text="Maximum times to send this email to one subscriber"
    )
    
    # Analytics
    total_triggered = models.PositiveIntegerField(default=0)
    total_sent = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Automated Email"
        verbose_name_plural = "Automated Emails"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_trigger_type_display()})"


class SubscriptionForm(models.Model):
    """Customizable subscription forms"""
    
    FORM_TYPES = [
        ('popup', 'Popup Modal'),
        ('inline', 'Inline Form'),
        ('sidebar', 'Sidebar Widget'),
        ('footer', 'Footer Form'),
        ('page', 'Dedicated Page'),
    ]
    
    name = models.CharField(max_length=200)
    form_type = models.CharField(max_length=20, choices=FORM_TYPES, default='inline')
    
    # Content
    headline = models.CharField(max_length=200, default="Subscribe to Our Newsletter")
    description = models.TextField(
        default="Get the latest blog posts and updates delivered to your inbox.",
        max_length=500
    )
    button_text = models.CharField(max_length=50, default="Subscribe")
    success_message = models.CharField(
        max_length=200,
        default="Thank you for subscribing! Please check your email to confirm."
    )
    
    # Display Settings
    show_name_fields = models.BooleanField(default=False)
    show_interests = models.BooleanField(default=False)
    require_double_opt_in = models.BooleanField(
        default=True,
        help_text="Send verification email before activation"
    )
    
    # Styling (basic customization)
    background_color = models.CharField(max_length=7, default="#ffffff", help_text="Hex color")
    text_color = models.CharField(max_length=7, default="#333333", help_text="Hex color")
    button_color = models.CharField(max_length=7, default="#007cba", help_text="Hex color")
    
    # Settings
    is_active = models.BooleanField(default=True)
    
    # Analytics
    total_views = models.PositiveIntegerField(default=0)
    total_submissions = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Subscription Form"
        verbose_name_plural = "Subscription Forms"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_form_type_display()})"
    
    def get_conversion_rate(self):
        if self.total_views > 0:
            return round((self.total_submissions / self.total_views) * 100, 1)
        return 0