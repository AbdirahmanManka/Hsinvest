from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from django.utils.safestring import mark_safe
from .models import (
    NewsletterSubscriber, EmailCampaign, EmailTemplate, 
    NewsletterActivity, AutomatedEmail, SubscriptionForm
)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Basic Information', {
            'fields': ('email', 'first_name', 'last_name', 'status')
        }),
        ('Preferences', {
            'fields': ('frequency_preference', 'subscription_interests')
        }),
        ('Technical Information', {
            'fields': ('ip_address', 'user_agent', 'referrer_url', 'country', 'city'),
            'classes': ('collapse',)
        }),
        ('Engagement Metrics', {
            'fields': ('total_emails_sent', 'total_emails_opened', 'total_links_clicked', 'last_engagement'),
            'classes': ('collapse',)
        }),
        ('Verification', {
            'fields': ('is_verified', 'verification_sent_at', 'verified_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('subscribed_at', 'unsubscribed_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_display = (
        'email', 'get_full_name', 'status_colored', 'status', 'is_verified', 
        'engagement_rate_display', 'frequency_preference', 'subscribed_at'
    )
    list_filter = ('status', 'is_verified', 'frequency_preference', 'country', 'subscribed_at')
    search_fields = ('email', 'first_name', 'last_name')
    readonly_fields = ('subscription_token', 'subscribed_at', 'unsubscribed_at', 'updated_at')
    list_editable = ('status',)
    ordering = ['-subscribed_at']
    date_hierarchy = 'subscribed_at'
    
    def status_colored(self, obj):
        colors = {
            'active': 'green',
            'unsubscribed': 'red',
            'bounced': 'orange',
            'spam_complaint': 'purple'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = "Status"
    
    def engagement_rate_display(self, obj):
        rate = obj.get_engagement_rate()
        if rate > 50:
            color = 'green'
        elif rate > 20:
            color = 'orange'
        else:
            color = 'red'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, rate)
    engagement_rate_display.short_description = "Engagement"
    
    actions = ['activate_subscribers', 'deactivate_subscribers', 'export_subscribers']
    
    def activate_subscribers(self, request, queryset):
        queryset.update(status='active')
        self.message_user(request, f"{queryset.count()} subscribers activated.")
    activate_subscribers.short_description = "Activate selected subscribers"
    
    def deactivate_subscribers(self, request, queryset):
        queryset.update(status='unsubscribed')
        self.message_user(request, f"{queryset.count()} subscribers deactivated.")
    deactivate_subscribers.short_description = "Deactivate selected subscribers"
    
    def export_subscribers(self, request, queryset):
        # This would implement CSV export functionality
        self.message_user(request, f"{queryset.count()} subscribers selected for export.")
    export_subscribers.short_description = "Export selected subscribers"


@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Campaign Details', {
            'fields': ('name', 'campaign_type', 'subject', 'preheader')
        }),
        ('Content', {
            'fields': ('content', 'plain_text_content')
        }),
        ('Sender Information', {
            'fields': ('from_name', 'from_email', 'reply_to_email')
        }),
        ('Targeting', {
            'fields': ('send_to_all', 'target_categories', 'target_subscribers'),
            'classes': ('collapse',)
        }),
        ('Scheduling', {
            'fields': ('status', 'scheduled_at', 'sent_at')
        }),
        ('Analytics', {
            'fields': (
                'total_recipients', 'total_sent', 'total_delivered', 'total_bounced',
                'total_opened', 'total_clicked', 'total_unsubscribed', 'total_spam_complaints'
            ),
            'classes': ('collapse',)
        }),
        ('Featured Content', {
            'fields': ('featured_posts',),
            'classes': ('collapse',)
        }),
    )
    
    list_display = (
        'name', 'campaign_type', 'status_colored', 'total_recipients',
        'open_rate_display', 'click_rate_display', 'scheduled_at', 'sent_at'
    )
    list_filter = ('campaign_type', 'status', 'created_at', 'scheduled_at')
    search_fields = ('name', 'subject', 'content')
    readonly_fields = ('sent_at', 'created_at', 'updated_at')
    ordering = ['-created_at']
    
    def status_colored(self, obj):
        colors = {
            'draft': 'gray',
            'scheduled': 'blue',
            'sending': 'orange',
            'sent': 'green',
            'paused': 'orange',
            'cancelled': 'red'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = "Status"
    
    def open_rate_display(self, obj):
        rate = obj.get_open_rate()
        if rate > 25:
            color = 'green'
        elif rate > 15:
            color = 'orange'
        else:
            color = 'red'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, rate)
    open_rate_display.short_description = "Open Rate"
    
    def click_rate_display(self, obj):
        rate = obj.get_click_rate()
        if rate > 5:
            color = 'green'
        elif rate > 2:
            color = 'orange'
        else:
            color = 'red'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, rate)
    click_rate_display.short_description = "Click Rate"
    
    actions = ['duplicate_campaign', 'send_test_email', 'send_campaign']
    
    def duplicate_campaign(self, request, queryset):
        for campaign in queryset:
            campaign.pk = None
            campaign.name = f"Copy of {campaign.name}"
            campaign.status = 'draft'
            campaign.scheduled_at = None
            campaign.sent_at = None
            campaign.save()
        self.message_user(request, f"{queryset.count()} campaigns duplicated.")
    duplicate_campaign.short_description = "Duplicate selected campaigns"
    
    def send_test_email(self, request, queryset):
        from .services import NewsletterService
        
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one campaign for test email.", level='ERROR')
            return
        
        campaign = queryset.first()
        if campaign.status != 'draft':
            self.message_user(request, "Only draft campaigns can be used for test emails.", level='ERROR')
            return
        
        # Get test email from request
        test_email = request.POST.get('test_email')
        if not test_email:
            self.message_user(request, "Please provide a test email address.", level='ERROR')
            return
        
        service = NewsletterService()
        result = service.send_test_email(campaign.id, test_email)
        
        if result['success']:
            self.message_user(request, result['message'], level='SUCCESS')
        else:
            self.message_user(request, result['message'], level='ERROR')
    send_test_email.short_description = "Send test email"
    
    def send_campaign(self, request, queryset):
        from .services import NewsletterService
        
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one campaign to send.", level='ERROR')
            return
        
        campaign = queryset.first()
        if campaign.status != 'draft':
            self.message_user(request, "Only draft campaigns can be sent.", level='ERROR')
            return
        
        service = NewsletterService()
        result = service.send_campaign(campaign.id)
        
        if result['success']:
            self.message_user(request, result['message'], level='SUCCESS')
        else:
            self.message_user(request, result['message'], level='ERROR')
    send_campaign.short_description = "Send campaign to subscribers"


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'is_active', 'is_default', 'times_used', 'updated_at')
    list_filter = ('template_type', 'is_active', 'is_default', 'created_at')
    search_fields = ('name', 'description', 'subject_template')
    list_editable = ('is_active', 'is_default')
    ordering = ['template_type', 'name']
    
    def save_model(self, request, obj, form, change):
        # Ensure only one default template per type
        if obj.is_default:
            EmailTemplate.objects.filter(
                template_type=obj.template_type,
                is_default=True
            ).exclude(pk=obj.pk).update(is_default=False)
        super().save_model(request, obj, form, change)


@admin.register(NewsletterActivity)
class NewsletterActivityAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'activity_type_colored', 'campaign', 'email_subject_short', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('subscriber__email', 'description', 'email_subject', 'campaign__name')
    readonly_fields = ('created_at',)
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def activity_type_colored(self, obj):
        colors = {
            'subscription': 'green',
            'unsubscription': 'red',
            'email_sent': 'blue',
            'email_opened': 'orange',
            'link_clicked': 'purple',
            'bounce': 'red',
            'spam_complaint': 'red',
            'verification_sent': 'blue',
            'email_verified': 'green'
        }
        color = colors.get(obj.activity_type, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_activity_type_display()
        )
    activity_type_colored.short_description = "Activity Type"
    
    def email_subject_short(self, obj):
        if obj.email_subject:
            return obj.email_subject[:30] + "..." if len(obj.email_subject) > 30 else obj.email_subject
        return "-"
    email_subject_short.short_description = "Subject"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AutomatedEmail)
class AutomatedEmailAdmin(admin.ModelAdmin):
    list_display = ('name', 'trigger_type', 'email_template', 'is_active', 'delay_hours', 'total_sent')
    list_filter = ('trigger_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    ordering = ['name']


@admin.register(SubscriptionForm)
class SubscriptionFormAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Basic Settings', {
            'fields': ('name', 'form_type', 'is_active')
        }),
        ('Content', {
            'fields': ('headline', 'description', 'button_text', 'success_message')
        }),
        ('Form Options', {
            'fields': ('show_name_fields', 'show_interests', 'require_double_opt_in')
        }),
        ('Styling', {
            'fields': ('background_color', 'text_color', 'button_color'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('total_views', 'total_submissions'),
            'classes': ('collapse',)
        }),
    )
    
    list_display = ('name', 'form_type', 'is_active', 'conversion_rate_display', 'total_submissions', 'updated_at')
    list_filter = ('form_type', 'is_active', 'created_at')
    search_fields = ('name', 'headline', 'description')
    list_editable = ('is_active',)
    ordering = ['name']
    
    def conversion_rate_display(self, obj):
        rate = obj.get_conversion_rate()
        if rate > 5:
            color = 'green'
        elif rate > 2:
            color = 'orange'
        else:
            color = 'red'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, rate)
    conversion_rate_display.short_description = "Conversion Rate"