from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from blog.models import BlogPost
from core.models import Page
import json
from datetime import datetime, timedelta


class PageView(models.Model):
    """Track page views across the entire site"""
    
    PAGE_TYPES = [
        ('home', 'Homepage'),
        ('blog_list', 'Blog List'),
        ('blog_post', 'Blog Post'),
        ('category', 'Category Page'),
        ('tag', 'Tag Page'),
        ('page', 'Static Page'),
        ('other', 'Other'),
    ]
    
    # Page Information
    page_type = models.CharField(max_length=20, choices=PAGE_TYPES, default='other')
    page_title = models.CharField(max_length=200, blank=True)
    url = models.URLField()
    
    # Content References (optional, for specific content)
    blog_post = models.ForeignKey(
        BlogPost, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='analytics_views'
    )
    page = models.ForeignKey(
        Page, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='analytics_views'
    )
    
    # Visitor Information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    
    # User Information (if logged in)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='page_views'
    )
    
    # Session Information
    session_key = models.CharField(max_length=40, blank=True)
    
    # Location Data (can be populated by GeoIP service)
    country_code = models.CharField(max_length=2, blank=True)
    country_name = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    
    # Device Information
    device_type = models.CharField(max_length=20, blank=True)  # mobile, tablet, desktop
    browser = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=50, blank=True)
    
    # Timing Information
    time_on_page = models.PositiveIntegerField(default=0, help_text="Time spent on page in seconds")
    
    # Engagement Metrics
    scroll_depth = models.PositiveSmallIntegerField(default=0, help_text="Max scroll depth percentage")
    bounced = models.BooleanField(default=True, help_text="Single page session")
    
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Page View"
        verbose_name_plural = "Page Views"
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['viewed_at']),
            models.Index(fields=['page_type', 'viewed_at']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['session_key']),
        ]
    
    def __str__(self):
        return f"{self.page_title or self.url} - {self.viewed_at}"
    
    def is_unique_visitor(self):
        """Check if this is a unique visitor for the day"""
        today = timezone.now().date()
        return not PageView.objects.filter(
            ip_address=self.ip_address,
            viewed_at__date=today
        ).exclude(id=self.id).exists()
    
    def get_device_icon(self):
        """Return icon for device type"""
        icons = {
            'mobile': '📱',
            'tablet': '📟',
            'desktop': '💻'
        }
        return icons.get(self.device_type.lower(), '❓')


class SearchQuery(models.Model):
    """Track search queries on the site"""
    
    query = models.CharField(max_length=200)
    results_count = models.PositiveIntegerField(default=0)
    
    # Visitor Information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    
    # User Information (if logged in)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='search_queries'
    )
    
    searched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Search Query"
        verbose_name_plural = "Search Queries"
        ordering = ['-searched_at']
    
    def __str__(self):
        return f'"{self.query}" ({self.results_count} results)'


class DownloadEvent(models.Model):
    """Track file downloads and resource access"""
    
    DOWNLOAD_TYPES = [
        ('blog_resource', 'Blog Resource'),
        ('pdf', 'PDF Document'),
        ('image', 'Image'),
        ('other', 'Other File'),
    ]
    
    # File Information
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField(default=0, help_text="File size in bytes")
    download_type = models.CharField(max_length=20, choices=DOWNLOAD_TYPES, default='other')
    
    # Content Reference
    blog_post = models.ForeignKey(
        BlogPost, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='download_events'
    )
    
    # Visitor Information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    
    # User Information (if logged in)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='downloads'
    )
    
    downloaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Download Event"
        verbose_name_plural = "Download Events"
        ordering = ['-downloaded_at']
    
    def __str__(self):
        return f"Download: {self.file_name}"
    
    def get_file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)


class SocialShare(models.Model):
    """Track social media shares"""
    
    PLATFORMS = [
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter/X'),
        ('linkedin', 'LinkedIn'),
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('email', 'Email'),
        ('copy_link', 'Copy Link'),
        ('other', 'Other'),
    ]
    
    platform = models.CharField(max_length=20, choices=PLATFORMS)
    
    # Content Information
    shared_url = models.URLField()
    content_title = models.CharField(max_length=200, blank=True)
    
    # Content Reference
    blog_post = models.ForeignKey(
        BlogPost, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='social_shares'
    )
    page = models.ForeignKey(
        Page, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='social_shares'
    )
    
    # Visitor Information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # User Information (if logged in)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='social_shares'
    )
    
    shared_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Social Share"
        verbose_name_plural = "Social Shares"
        ordering = ['-shared_at']
    
    def __str__(self):
        return f"{self.get_platform_display()}: {self.content_title or self.shared_url}"
    
    def get_platform_icon(self):
        icons = {
            'facebook': '📘',
            'twitter': '🐦',
            'linkedin': '💼',
            'whatsapp': '💬',
            'telegram': '✈️',
            'email': '📧',
            'copy_link': '🔗'
        }
        return icons.get(self.platform, '📤')


class NewsletterStats(models.Model):
    """Track newsletter subscription statistics"""
    
    EVENT_TYPES = [
        ('subscription', 'New Subscription'),
        ('unsubscription', 'Unsubscription'),
        ('email_sent', 'Email Sent'),
        ('email_opened', 'Email Opened'),
        ('link_clicked', 'Link Clicked'),
    ]
    
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    email = models.EmailField()
    
    # Additional Data
    campaign_name = models.CharField(max_length=100, blank=True)
    email_subject = models.CharField(max_length=200, blank=True)
    link_url = models.URLField(blank=True)
    
    # Visitor Information
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Newsletter Stats"
        verbose_name_plural = "Newsletter Statistics"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_event_type_display()}: {self.email}"


class AnalyticsReport(models.Model):
    """Periodic analytics reports for performance tracking"""
    
    REPORT_TYPES = [
        ('daily', 'Daily Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
    ]
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    report_date = models.DateField()
    
    # Traffic Metrics
    total_views = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    bounce_rate = models.FloatField(default=0.0)
    avg_session_duration = models.PositiveIntegerField(default=0)
    
    # Content Metrics
    most_popular_posts = models.JSONField(default=list)
    top_search_queries = models.JSONField(default=list)
    top_referrers = models.JSONField(default=list)
    
    # Engagement Metrics
    total_comments = models.PositiveIntegerField(default=0)
    total_ratings = models.PositiveIntegerField(default=0)
    total_shares = models.PositiveIntegerField(default=0)
    total_downloads = models.PositiveIntegerField(default=0)
    
    # Geographic Data
    top_countries = models.JSONField(default=list)
    top_cities = models.JSONField(default=list)
    
    # Technical Data
    top_browsers = models.JSONField(default=list)
    top_devices = models.JSONField(default=list)
    
    # Generated timestamp
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Analytics Report"
        verbose_name_plural = "Analytics Reports"
        ordering = ['-report_date']
        unique_together = ['report_type', 'report_date']
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.report_date}"


class GoogleAnalyticsIntegration(models.Model):
    """Store Google Analytics configuration and data"""
    
    # Configuration
    tracking_id = models.CharField(max_length=50, help_text="GA tracking ID (G-XXXXXXXXXX)")
    property_id = models.CharField(max_length=50, blank=True, help_text="GA4 Property ID")
    is_active = models.BooleanField(default=True)
    
    # API Configuration (for reporting)
    service_account_key = models.TextField(blank=True, help_text="JSON service account key")
    view_id = models.CharField(max_length=50, blank=True, help_text="GA View ID for reporting")
    
    # Last sync information
    last_sync = models.DateTimeField(blank=True, null=True)
    sync_status = models.CharField(max_length=100, blank=True)
    
    # Cached metrics (updated periodically)
    cached_metrics = models.JSONField(default=dict, help_text="Cached GA metrics")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Google Analytics Integration"
        verbose_name_plural = "Google Analytics Integrations"
    
    def __str__(self):
        return f"GA Integration - {self.tracking_id}"
    
    def is_configured(self):
        return bool(self.tracking_id and self.is_active)


# Utility functions for analytics
def get_popular_content(days=30):
    """Get most popular blog posts in the last N days"""
    from django.db.models import Count
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    popular_posts = PageView.objects.filter(
        page_type='blog_post',
        blog_post__isnull=False,
        viewed_at__gte=cutoff_date
    ).values(
        'blog_post__id',
        'blog_post__title',
        'blog_post__slug'
    ).annotate(
        view_count=Count('id')
    ).order_by('-view_count')[:10]
    
    return list(popular_posts)


def get_traffic_summary(days=30):
    """Get traffic summary for the last N days"""
    cutoff_date = timezone.now() - timedelta(days=days)
    
    total_views = PageView.objects.filter(viewed_at__gte=cutoff_date).count()
    unique_visitors = PageView.objects.filter(
        viewed_at__gte=cutoff_date
    ).values('ip_address').distinct().count()
    
    return {
        'total_views': total_views,
        'unique_visitors': unique_visitors,
        'period_days': days,
    }