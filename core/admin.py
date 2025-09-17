from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    SiteConfiguration, Page, ContactMessage, 
    FAQ, Testimonial, Service
)


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Basic Information', {
            'fields': ('site_name', 'site_description', 'site_keywords')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'linkedin_url', 'instagram_url'),
            'classes': ('collapse',)
        }),
        ('SEO Settings', {
            'fields': ('meta_description', 'og_image'),
            'classes': ('collapse',)
        }),
        ('Site Features', {
            'fields': ('maintenance_mode', 'allow_comments', 'allow_newsletter_signup')
        }),
    )
    
    list_display = ('site_name', 'email', 'maintenance_mode', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    
    def has_add_permission(self, request):
        # Allow only one instance
        return not SiteConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'page_type', 'content')
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('is_published', 'show_in_menu', 'menu_order')
        }),
    )
    
    list_display = ('title', 'page_type', 'is_published', 'show_in_menu', 'created_at')
    list_filter = ('page_type', 'is_published', 'show_in_menu', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_published', 'show_in_menu')
    ordering = ['menu_order', 'title']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Message Details', {
            'fields': ('name', 'email', 'phone', 'subject', 'message')
        }),
        ('Status', {
            'fields': ('is_read', 'is_replied', 'admin_notes')
        }),
        ('Technical Info', {
            'fields': ('ip_address', 'user_agent', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_display = ('name', 'email', 'subject_short', 'is_read', 'is_replied', 'created_at')
    list_filter = ('is_read', 'is_replied', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at', 'updated_at', 'ip_address', 'user_agent')
    list_editable = ('is_read', 'is_replied')
    ordering = ['-created_at']
    
    def subject_short(self, obj):
        return obj.subject[:30] + "..." if len(obj.subject) > 30 else obj.subject
    subject_short.short_description = "Subject"
    
    actions = ['mark_as_read', 'mark_as_replied']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"{queryset.count()} messages marked as read.")
    mark_as_read.short_description = "Mark selected messages as read"
    
    def mark_as_replied(self, request, queryset):
        queryset.update(is_replied=True)
        self.message_user(request, f"{queryset.count()} messages marked as replied.")
    mark_as_replied.short_description = "Mark selected messages as replied"


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question_short', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('question', 'answer')
    list_editable = ('is_active', 'order')
    ordering = ['order', 'question']
    
    def question_short(self, obj):
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question
    question_short.short_description = "Question"


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'title', 'content', 'image', 'rating')
        }),
        ('Social Links', {
            'fields': ('website_url', 'linkedin_url'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'is_active', 'order')
        }),
    )
    
    list_display = ('name', 'title', 'rating_stars', 'is_featured', 'is_active', 'order', 'created_at')
    list_filter = ('rating', 'is_featured', 'is_active', 'created_at')
    search_fields = ('name', 'title', 'content')
    list_editable = ('is_featured', 'is_active', 'order')
    ordering = ['-is_featured', 'order', '-created_at']
    
    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: gold;">{}</span>', stars)
    rating_stars.short_description = "Rating"


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'content', 'image', 'icon')
        }),
        ('Pricing', {
            'fields': ('price_from', 'price_currency'),
            'classes': ('collapse',)
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'is_active', 'order')
        }),
    )
    
    list_display = ('title', 'price_display', 'is_featured', 'is_active', 'order', 'created_at')
    list_filter = ('is_featured', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'content')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_featured', 'is_active', 'order')
    ordering = ['-is_featured', 'order', 'title']
    
    def price_display(self, obj):
        if obj.price_from:
            return f"From {obj.price_currency} {obj.price_from}"
        return "Price on request"
    price_display.short_description = "Pricing"


# Customize admin site headers
admin.site.site_header = "Habiba's Blog Administration"
admin.site.site_title = "Blog Admin"
admin.site.index_title = "Welcome to Blog Administration"