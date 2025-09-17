from django.db import models
from django.utils import timezone
from ckeditor.fields import RichTextField
from django.core.validators import EmailValidator

class SiteConfiguration(models.Model):
    """Global site configuration settings"""
    site_name = models.CharField(max_length=100, default="Habiba's Blog")
    site_description = models.TextField(max_length=200, default="Welcome to my professional blog")
    site_keywords = models.CharField(max_length=200, help_text="SEO keywords, comma separated")
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Social Media Links
    facebook_url = models.URLField(blank=True, default="https://www.facebook.com/share/16JsHuJwh1/")
    twitter_url = models.URLField(blank=True, default="https://x.com/BarkhadleHabibo?t=dcVebF8tuOiQUGn67tC8dw&s=08")
    linkedin_url = models.URLField(blank=True, default="https://www.linkedin.com/in/habibo-barkadle-83428a213?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app")
    
    # SEO Settings
    meta_description = models.CharField(max_length=160, help_text="Meta description for SEO")
    og_image = models.ImageField(upload_to='site/', blank=True, help_text="Open Graph image")
    
    # Site Features
    maintenance_mode = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    allow_newsletter_signup = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"
    
    def __str__(self):
        return f"{self.site_name} Configuration"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if SiteConfiguration.objects.exists() and not self.pk:
            raise ValueError("Only one Site Configuration instance is allowed")
        return super().save(*args, **kwargs)


class Page(models.Model):
    """Static pages like About, Services, Privacy Policy, etc."""
    
    PAGE_TYPES = [
        ('about', 'About'),
        ('services', 'Services'),
        ('privacy', 'Privacy Policy'),
        ('terms', 'Terms of Service'),
        ('contact', 'Contact'),
        ('custom', 'Custom Page'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    page_type = models.CharField(max_length=20, choices=PAGE_TYPES, default='custom')
    content = RichTextField()
    
    # SEO Fields
    meta_title = models.CharField(max_length=60, blank=True, help_text="SEO title (60 chars)")
    meta_description = models.CharField(max_length=160, blank=True, help_text="SEO description (160 chars)")
    meta_keywords = models.CharField(max_length=200, blank=True, help_text="SEO keywords, comma separated")
    
    # Page Settings
    is_published = models.BooleanField(default=True)
    show_in_menu = models.BooleanField(default=False, help_text="Show in main navigation")
    menu_order = models.PositiveIntegerField(default=0, help_text="Order in menu (lower numbers first)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['menu_order', 'title']
        verbose_name = "Page"
        verbose_name_plural = "Pages"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.meta_title:
            self.meta_title = self.title[:60]
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class ContactMessage(models.Model):
    """Contact form submissions"""
    
    name = models.CharField(max_length=100)
    email = models.EmailField(validators=[EmailValidator()])
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    # Additional Info
    phone = models.CharField(max_length=20, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_replied = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, help_text="Internal notes for admin")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
    
    def __str__(self):
        return f"{self.name} - {self.subject[:30]}"


class FAQ(models.Model):
    """Frequently Asked Questions"""
    
    question = models.CharField(max_length=300)
    answer = RichTextField()
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers first)")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'question']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
    
    def __str__(self):
        return self.question[:50]


class Testimonial(models.Model):
    """Client testimonials"""
    
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, blank=True, help_text="Job title or company")
    content = models.TextField(max_length=500)
    image = models.ImageField(upload_to='testimonials/', blank=True)
    rating = models.PositiveSmallIntegerField(default=5, help_text="Rating out of 5")
    
    # Social Links
    website_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    
    # Display Settings
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', 'order', '-created_at']
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"
    
    def __str__(self):
        return f"{self.name} - {self.rating}★"


class Service(models.Model):
    """Services offered"""
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    description = models.TextField(max_length=300, help_text="Short description")
    content = RichTextField(help_text="Detailed service description")
    image = models.ImageField(upload_to='services/', blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="CSS class for icon (e.g., fas fa-code)")
    
    # Pricing
    price_from = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    price_currency = models.CharField(max_length=3, default='USD')
    
    # SEO
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    # Display Settings
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', 'order', 'title']
        verbose_name = "Service"
        verbose_name_plural = "Services"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        if not self.meta_title:
            self.meta_title = self.title[:60]
        super().save(*args, **kwargs)