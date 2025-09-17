from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from django.utils.safestring import mark_safe
import json
from .models import (
    PageView, SearchQuery, DownloadEvent, SocialShare, 
    NewsletterStats, AnalyticsReport, GoogleAnalyticsIntegration
)


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = (
        'page_title_short', 'page_type', 'device_icon_display', 'country_name', 
        'browser', 'time_on_page_display', 'user', 'viewed_at'
    )
    list_filter = ('page_type', 'device_type', 'browser', 'country_code', 'bounced', 'viewed_at')
    search_fields = ('page_title', 'url', 'ip_address', 'city', 'user__username')
    readonly_fields = ('viewed_at',)
    ordering = ['-viewed_at']
    date_hierarchy = 'viewed_at'
    
    # Custom list per page
    list_per_page = 50
    
    def page_title_short(self, obj):
        title = obj.page_title or obj.url
        return title[:50] + "..." if len(title) > 50 else title
    page_title_short.short_description = "Page"
    
    def device_icon_display(self, obj):
        icon = obj.get_device_icon()
        return format_html(f'{icon} {obj.device_type}')
    device_icon_display.short_description = "Device"
    
    def time_on_page_display(self, obj):
        if obj.time_on_page > 0:
            minutes = obj.time_on_page // 60
            seconds = obj.time_on_page % 60
            return f"{minutes}m {seconds}s"
        return "0s"
    time_on_page_display.short_description = "Time on Page"
    
    # Custom actions
    actions = ['export_as_csv']
    
    def export_as_csv(self, request, queryset):
        # This would implement CSV export functionality
        self.message_user(request, f"{queryset.count()} records selected for export.")
    export_as_csv.short_description = "Export selected views as CSV"
    
    def has_add_permission(self, request):
        return False


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'results_count', 'user', 'searched_at')
    list_filter = ('results_count', 'searched_at')
    search_fields = ('query', 'user__username')
    readonly_fields = ('searched_at',)
    ordering = ['-searched_at']
    
    def get_queryset(self, request):
        # Show popular searches by default
        return super().get_queryset(request).annotate(
            search_count=Count('query')
        )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DownloadEvent)
class DownloadEventAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'download_type', 'file_size_display', 'blog_post', 'user', 'downloaded_at')
    list_filter = ('download_type', 'downloaded_at')
    search_fields = ('file_name', 'blog_post__title', 'user__username')
    readonly_fields = ('downloaded_at',)
    ordering = ['-downloaded_at']
    
    def file_size_display(self, obj):
        size_mb = obj.get_file_size_mb()
        if size_mb > 1:
            return f"{size_mb} MB"
        else:
            return f"{obj.file_size} bytes"
    file_size_display.short_description = "File Size"
    
    def has_add_permission(self, request):
        return False


@admin.register(SocialShare)
class SocialShareAdmin(admin.ModelAdmin):
    list_display = ('platform_icon_display', 'content_title_short', 'blog_post', 'user', 'shared_at')
    list_filter = ('platform', 'shared_at')
    search_fields = ('content_title', 'shared_url', 'blog_post__title')
    readonly_fields = ('shared_at',)
    ordering = ['-shared_at']
    
    def platform_icon_display(self, obj):
        icon = obj.get_platform_icon()
        return format_html(f'{icon} {obj.get_platform_display()}')
    platform_icon_display.short_description = "Platform"
    
    def content_title_short(self, obj):
        title = obj.content_title or obj.shared_url
        return title[:40] + "..." if len(title) > 40 else title
    content_title_short.short_description = "Content"
    
    def has_add_permission(self, request):
        return False


@admin.register(NewsletterStats)
class NewsletterStatsAdmin(admin.ModelAdmin):
    list_display = ('event_type_colored', 'email', 'campaign_name', 'email_subject_short', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('email', 'campaign_name', 'email_subject')
    readonly_fields = ('created_at',)
    ordering = ['-created_at']
    
    def event_type_colored(self, obj):
        colors = {
            'subscription': 'green',
            'unsubscription': 'red',
            'email_sent': 'blue',
            'email_opened': 'orange',
            'link_clicked': 'purple'
        }
        color = colors.get(obj.event_type, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_event_type_display()
        )
    event_type_colored.short_description = "Event Type"
    
    def email_subject_short(self, obj):
        if obj.email_subject:
            return obj.email_subject[:30] + "..." if len(obj.email_subject) > 30 else obj.email_subject
        return "-"
    email_subject_short.short_description = "Subject"
    
    def has_add_permission(self, request):
        return False


@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = (
        'report_type', 'report_date', 'total_views', 'unique_visitors', 
        'bounce_rate_display', 'total_comments', 'generated_at'
    )
    list_filter = ('report_type', 'report_date', 'generated_at')
    readonly_fields = ('generated_at',)
    ordering = ['-report_date']
    
    def bounce_rate_display(self, obj):
        return f"{obj.bounce_rate:.1f}%"
    bounce_rate_display.short_description = "Bounce Rate"
    
    # Custom view for report details
    def view_on_site(self, obj):
        # This would link to a custom analytics dashboard
        return reverse('admin:analytics_report_detail', args=[obj.id])


@admin.register(GoogleAnalyticsIntegration)
class GoogleAnalyticsIntegrationAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Basic Configuration', {
            'fields': ('tracking_id', 'property_id', 'is_active')
        }),
        ('API Configuration', {
            'fields': ('service_account_key', 'view_id'),
            'classes': ('collapse',),
            'description': 'Optional: For importing data from Google Analytics'
        }),
        ('Sync Status', {
            'fields': ('last_sync', 'sync_status'),
            'classes': ('collapse',)
        }),
        ('Cached Data', {
            'fields': ('cached_metrics',),
            'classes': ('collapse',)
        }),
    )
    
    list_display = ('tracking_id', 'is_active', 'last_sync_display', 'created_at')
    list_filter = ('is_active', 'last_sync')
    readonly_fields = ('last_sync', 'created_at', 'updated_at')
    
    def last_sync_display(self, obj):
        if obj.last_sync:
            return obj.last_sync.strftime('%Y-%m-%d %H:%M')
        return "Never"
    last_sync_display.short_description = "Last Sync"
    
    def has_add_permission(self, request):
        # Allow only one GA integration
        return not GoogleAnalyticsIntegration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return True
    
    actions = ['sync_with_ga']
    
    def sync_with_ga(self, request, queryset):
        # This would implement GA sync functionality
        self.message_user(request, "Google Analytics sync initiated.")
    sync_with_ga.short_description = "Sync with Google Analytics"


# Custom admin views for analytics dashboard
# Note: Custom admin config would be implemented separately if needed

# Create summary views
def analytics_summary():
    """Create analytics summary for admin dashboard"""
    from datetime import timedelta
    from django.utils import timezone
    
    # Last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    summary = {
        'total_views': PageView.objects.filter(viewed_at__gte=thirty_days_ago).count(),
        'unique_visitors': PageView.objects.filter(
            viewed_at__gte=thirty_days_ago
        ).values('ip_address').distinct().count(),
        'total_searches': SearchQuery.objects.filter(searched_at__gte=thirty_days_ago).count(),
        'total_downloads': DownloadEvent.objects.filter(downloaded_at__gte=thirty_days_ago).count(),
        'total_shares': SocialShare.objects.filter(shared_at__gte=thirty_days_ago).count(),
    }
    
    return summary

# Make summary available to templates
admin.site.analytics_summary = analytics_summary