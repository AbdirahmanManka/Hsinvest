from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from ckeditor_uploader.fields import RichTextUploadingField
from taggit.managers import TaggableManager
from django.core.validators import MinValueValidator, MaxValueValidator
import os


class Category(models.Model):
    """Blog post categories"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True)
    
    # SEO fields
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    # Display settings
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.meta_title:
            self.meta_title = self.name
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:category_detail', kwargs={'slug': self.slug})
    
    def get_post_count(self):
        return self.blogpost_set.filter(status='published').count()


class BlogPost(models.Model):
    """Main blog post model"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('scheduled', 'Scheduled'),
        ('archived', 'Archived'),
    ]
    
    # Basic fields
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200, blank=True)
    excerpt = models.TextField(blank=True, null=True, help_text="Short description for post preview")
    content = RichTextUploadingField()
    
    # Media
    featured_image = models.ImageField(
        upload_to='blog/featured/', 
        max_length=255,
        blank=True,
        null=True,
        help_text="Main image for the post"
    )
    featured_image_alt = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Alt text for featured image (SEO)"
    )
    
    # Relationships
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags = TaggableManager(blank=True)
    
    # Publishing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(blank=True, null=True)
    scheduled_at = models.DateTimeField(
        blank=True, 
        null=True,
        help_text="Schedule post to be published at this time"
    )
    
    # SEO fields
    meta_title = models.CharField(max_length=60, blank=True, help_text="SEO title")
    meta_description = models.CharField(max_length=160, blank=True, help_text="SEO description")
    meta_keywords = models.CharField(max_length=200, blank=True)
    
    # Settings
    allow_comments = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Show in featured posts")
    reading_time = models.PositiveIntegerField(default=0, help_text="Estimated reading time in minutes")
    
    # Analytics
    views_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug with uniqueness check
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            
            # Check if slug exists and make it unique
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
            
        # Set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
            
        # Auto-generate meta fields
        if not self.meta_title:
            self.meta_title = self.title[:60]
        if not self.meta_description:
            self.meta_description = self.excerpt[:160]
            
        # Calculate reading time (average 200 words per minute)
        if self.content:
            word_count = len(self.content.split())
            self.reading_time = max(1, word_count // 200)
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})
    
    def get_previous_post(self):
        return BlogPost.objects.filter(
            status='published',
            published_at__lt=self.published_at
        ).order_by('-published_at').first()
    
    def get_next_post(self):
        return BlogPost.objects.filter(
            status='published',
            published_at__gt=self.published_at
        ).order_by('published_at').first()
    
    def get_related_posts(self, count=3):
        """Get related posts based on tags and category"""
        related = BlogPost.objects.filter(
            status='published'
        ).exclude(id=self.id)
        
        # First try to get posts from same category
        if self.category:
            related = related.filter(category=self.category)
        
        # If not enough posts, get by tags
        if related.count() < count:
            tag_names = self.tags.names()
            if tag_names:
                related = BlogPost.objects.filter(
                    tags__name__in=tag_names,
                    status='published'
                ).exclude(id=self.id).distinct()
        
        return related[:count]
    
    def get_average_rating(self):
        ratings = self.ratings.all()
        if ratings.exists():
            return round(ratings.aggregate(models.Avg('stars'))['stars__avg'], 1)
        return 0
    
    def get_rating_count(self):
        return self.ratings.count()


class BlogResource(models.Model):
    """Resources attached to blog posts (PDFs, links, files)"""
    
    RESOURCE_TYPES = [
        ('file', 'File'),
        ('link', 'External Link'),
        ('pdf', 'PDF Document'),
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default='file')
    
    # File upload
    file = models.FileField(upload_to='blog/resources/', blank=True)
    
    # External link
    external_url = models.URLField(blank=True)
    
    # Display settings
    order = models.PositiveIntegerField(default=0)
    is_downloadable = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'title']
        verbose_name = "Blog Resource"
        verbose_name_plural = "Blog Resources"
    
    def __str__(self):
        return f"{self.post.title} - {self.title}"
    
    def get_file_size(self):
        if self.file:
            return self.file.size
        return 0
    
    def get_file_extension(self):
        if self.file:
            return os.path.splitext(self.file.name)[1][1:].upper()
        return ""


class Comment(models.Model):
    """Blog post comments with threading support"""
    
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies'
    )
    
    # Comment details
    name = models.CharField(max_length=100)
    email = models.EmailField()
    website = models.URLField(blank=True)
    content = models.TextField(max_length=1000)
    
    # Moderation
    is_approved = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False)
    
    # Technical info
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
    
    def __str__(self):
        return f"{self.name} on {self.post.title}"
    
    def get_replies(self):
        return self.replies.filter(is_approved=True).order_by('created_at')


class Rating(models.Model):
    """Blog post ratings"""
    
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='ratings')
    
    # Rating details
    stars = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    
    # User identification (anonymous users)
    user_identifier = models.CharField(
        max_length=100, 
        help_text="IP address or session key for anonymous users"
    )
    user_name = models.CharField(max_length=100, blank=True)
    user_email = models.EmailField(blank=True)
    
    # Optional review text
    review_text = models.TextField(max_length=500, blank=True)
    
    # Technical info
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['post', 'user_identifier']
        ordering = ['-created_at']
        verbose_name = "Rating"
        verbose_name_plural = "Ratings"
    
    def __str__(self):
        return f"{self.stars}★ for {self.post.title}"


class BlogView(models.Model):
    """Track blog post views for analytics"""
    
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='blog_views')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    
    # Location data (can be populated by external service)
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Blog View"
        verbose_name_plural = "Blog Views"
        indexes = [
            models.Index(fields=['post', 'viewed_at']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        return f"View of {self.post.title} from {self.ip_address}"