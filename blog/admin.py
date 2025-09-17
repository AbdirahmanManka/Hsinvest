from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models
from .models import (
    Category, BlogPost, BlogResource, Comment, Rating, BlogView
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'image')
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('is_active', 'order')
        }),
    )
    
    list_display = ('name', 'post_count', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'order')
    ordering = ['order', 'name']
    
    def post_count(self, obj):
        count = obj.get_post_count()
        return format_html(
            '<a href="{}?category__id__exact={}">{} posts</a>',
            reverse('admin:blog_blogpost_changelist'),
            obj.id,
            count
        )
    post_count.short_description = "Posts"


class BlogResourceInline(admin.TabularInline):
    model = BlogResource
    extra = 1
    fields = ('title', 'resource_type', 'file', 'external_url', 'order', 'is_downloadable')


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'author')
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_image_alt'),
        }),
        ('Classification', {
            'fields': ('category', 'tags')
        }),
        ('Publishing', {
            'fields': ('status', 'published_at', 'scheduled_at')
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('allow_comments', 'is_featured', 'reading_time'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('views_count',),
            'classes': ('collapse',)
        }),
    )
    
    list_display = (
        'title', 'author', 'category', 'status', 'is_featured', 
        'comment_count', 'rating_display', 'views_count', 'published_at'
    )
    list_filter = ('status', 'is_featured', 'category', 'allow_comments', 'created_at', 'published_at')
    search_fields = ('title', 'content', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('status', 'is_featured')
    date_hierarchy = 'published_at'
    ordering = ['-created_at']
    readonly_fields = ('views_count', 'reading_time')
    
    inlines = [BlogResourceInline]
    
    # Custom filter for author
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "author":
            kwargs["initial"] = request.user.id
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def comment_count(self, obj):
        count = obj.comments.filter(is_approved=True).count()
        if count > 0:
            return format_html(
                '<a href="{}?post__id__exact={}">{} comments</a>',
                reverse('admin:blog_comment_changelist'),
                obj.id,
                count
            )
        return "0 comments"
    comment_count.short_description = "Comments"
    
    def rating_display(self, obj):
        avg_rating = obj.get_average_rating()
        count = obj.get_rating_count()
        if avg_rating > 0:
            stars = '★' * int(avg_rating) + '☆' * (5 - int(avg_rating))
            return format_html(
                '<span style="color: gold;">{}</span> ({:.1f}/5, {} votes)',
                stars, avg_rating, count
            )
        return "No ratings"
    rating_display.short_description = "Rating"
    
    actions = ['make_published', 'make_draft', 'make_featured']
    
    def make_published(self, request, queryset):
        queryset.update(status='published')
        self.message_user(request, f"{queryset.count()} posts marked as published.")
    make_published.short_description = "Mark selected posts as published"
    
    def make_draft(self, request, queryset):
        queryset.update(status='draft')
        self.message_user(request, f"{queryset.count()} posts marked as draft.")
    make_draft.short_description = "Mark selected posts as draft"
    
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} posts marked as featured.")
    make_featured.short_description = "Mark selected posts as featured"


@admin.register(BlogResource)
class BlogResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'post', 'resource_type', 'file_info', 'order', 'is_downloadable')
    list_filter = ('resource_type', 'is_downloadable', 'created_at')
    search_fields = ('title', 'description', 'post__title')
    list_editable = ('order', 'is_downloadable')
    ordering = ['post', 'order']
    
    def file_info(self, obj):
        if obj.file:
            size_mb = obj.get_file_size() / (1024 * 1024)
            return f"{obj.get_file_extension()} ({size_mb:.1f} MB)"
        elif obj.external_url:
            return "External Link"
        return "No file"
    file_info.short_description = "File Info"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Comment Details', {
            'fields': ('post', 'parent', 'name', 'email', 'website', 'content')
        }),
        ('Moderation', {
            'fields': ('is_approved', 'is_spam')
        }),
        ('Technical Info', {
            'fields': ('ip_address', 'user_agent', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_display = ('name', 'post', 'content_preview', 'is_approved', 'is_spam', 'created_at')
    list_filter = ('is_approved', 'is_spam', 'created_at')
    search_fields = ('name', 'email', 'content', 'post__title')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_approved', 'is_spam')
    ordering = ['-created_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = "Content"
    
    actions = ['approve_comments', 'mark_as_spam']
    
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True, is_spam=False)
        self.message_user(request, f"{queryset.count()} comments approved.")
    approve_comments.short_description = "Approve selected comments"
    
    def mark_as_spam(self, request, queryset):
        queryset.update(is_spam=True, is_approved=False)
        self.message_user(request, f"{queryset.count()} comments marked as spam.")
    mark_as_spam.short_description = "Mark selected comments as spam"


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('post', 'stars_display', 'user_name', 'user_identifier', 'created_at')
    list_filter = ('stars', 'created_at')
    search_fields = ('post__title', 'user_name', 'user_email', 'review_text')
    readonly_fields = ('created_at', 'ip_address', 'user_agent')
    ordering = ['-created_at']
    
    def stars_display(self, obj):
        stars = '★' * obj.stars + '☆' * (5 - obj.stars)
        return format_html('<span style="color: gold;">{}</span>', stars)
    stars_display.short_description = "Rating"


@admin.register(BlogView)
class BlogViewAdmin(admin.ModelAdmin):
    list_display = ('post', 'ip_address', 'country', 'city', 'viewed_at')
    list_filter = ('country', 'viewed_at')
    search_fields = ('post__title', 'ip_address', 'city')
    readonly_fields = ('viewed_at',)
    ordering = ['-viewed_at']
    date_hierarchy = 'viewed_at'
    
    # Make it read-only for most users
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False