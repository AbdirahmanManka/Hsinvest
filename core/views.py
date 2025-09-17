from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, FormView
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from django.utils.html import strip_tags
from .models import Page, Service, Testimonial, FAQ, ContactMessage, SiteConfiguration
from blog.models import BlogPost
from newsletter.models import NewsletterSubscriber
from django.contrib.auth.mixins import LoginRequiredMixin


class HomeView(TemplateView):
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get featured blog posts
        context['featured_posts'] = BlogPost.objects.filter(
            status='published',
            is_featured=True
        ).order_by('-published_at')[:3]
        
        # Get latest blog posts
        context['latest_posts'] = BlogPost.objects.filter(
            status='published'
        ).order_by('-published_at')[:6]
        
        # Get featured services
        context['featured_services'] = Service.objects.filter(
            is_active=True,
            is_featured=True
        ).order_by('order')[:3]
        
        # Get testimonials
        context['testimonials'] = Testimonial.objects.filter(
            is_active=True
        ).order_by('-is_featured', 'order')[:6]
        
        # Site configuration
        try:
            context['site_config'] = SiteConfiguration.objects.first()
        except SiteConfiguration.DoesNotExist:
            context['site_config'] = None
            
        return context


class AboutView(TemplateView):
    template_name = 'core/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            context['page'] = Page.objects.get(page_type='about', is_published=True)
        except Page.DoesNotExist:
            context['page'] = None
            
        
        # Get testimonials
        context['testimonials'] = Testimonial.objects.filter(
            is_active=True
        ).order_by('-is_featured', 'order')[:4]
        
        return context


class ServicesView(TemplateView):
    template_name = 'core/services.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            context['page'] = Page.objects.get(page_type='services', is_published=True)
        except Page.DoesNotExist:
            context['page'] = None
            
        # Get all active services
        context['services'] = Service.objects.filter(
            is_active=True
        ).order_by('-is_featured', 'order')
        
        return context


class ContactView(TemplateView):
    template_name = 'core/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            context['page'] = Page.objects.get(page_type='contact', is_published=True)
        except Page.DoesNotExist:
            context['page'] = None
            
        # Site configuration for contact info
        try:
            context['site_config'] = SiteConfiguration.objects.first()
        except SiteConfiguration.DoesNotExist:
            context['site_config'] = None
            
        return context


class ContactFormView(FormView):
    template_name = 'core/contact.html'
    success_url = reverse_lazy('core:contact')
    
    def post(self, request, *args, **kwargs):
        # Get form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        phone = request.POST.get('phone', '')
        
        # Validate required fields
        if not all([name, email, subject, message]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('core:contact')
        
        try:
            # Create contact message in database
            contact_message = ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message,
                phone=phone,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Send email notification to admin
            self.send_contact_notification(contact_message)
            
            messages.success(request, 'Thank you for your message! We\'ll get back to you soon.')
            
        except BadHeaderError:
            messages.error(request, 'Invalid header found. Please try again.')
        except Exception as e:
            messages.error(request, 'Sorry, there was an error sending your message. Please try again later.')
            print(f"Contact form error: {e}")  # For debugging
            
        return redirect('core:contact')
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def send_contact_notification(self, contact_message):
        """Send email notification to admin when someone submits contact form"""
        try:
            # Email subject
            subject = f"New Contact Message: {contact_message.subject}"
            
            # Plain text message
            plain_message = f"""
New contact form submission from your blog:

Name: {contact_message.name}
Email: {contact_message.email}
Phone: {contact_message.phone or 'Not provided'}
Subject: {contact_message.subject}
Date: {contact_message.created_at.strftime('%B %d, %Y at %I:%M %p')}

Message:
{contact_message.message}

---
Reply directly to: {contact_message.email}
This is an automated notification from your blog's contact form.
            """
            
            # HTML message (optional, looks better)
            html_message = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #2563eb;">New Contact Message</h2>
    <p>Someone has sent you a message through your website contact form!</p>
    
    <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="color: #1e40af; margin-top: 0;">Message Details:</h3>
        <p><strong>Name:</strong> {contact_message.name}</p>
        <p><strong>Email:</strong> <a href="mailto:{contact_message.email}">{contact_message.email}</a></p>
        <p><strong>Phone:</strong> {contact_message.phone or 'Not provided'}</p>
        <p><strong>Subject:</strong> {contact_message.subject}</p>
        <p><strong>Date:</strong> {contact_message.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>
    
    <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="color: #1e40af; margin-top: 0;">Message:</h3>
        <p style="white-space: pre-wrap; line-height: 1.6;">{contact_message.message}</p>
    </div>
    
    <div style="background-color: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <p style="margin: 0; color: #92400e;"><strong>Quick Actions:</strong></p>
        <p style="margin: 5px 0 0 0; color: #92400e;">
            • Reply directly to: <a href="mailto:{contact_message.email}" style="color: #1e40af;">{contact_message.email}</a><br>
            • View in admin panel for more details
        </p>
    </div>
    
    <p style="color: #6b7280; font-size: 14px;">
        This is an automated notification from your blog's contact form.
    </p>
</div>
            """
            
            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[settings.EMAIL_HOST_USER],  # Send to yourself
                fail_silently=False,
            )
            
            print(f"Contact notification sent successfully to {settings.EMAIL_HOST_USER}")
            
        except Exception as e:
            print(f"Error sending contact notification: {e}")
            # Re-raise the exception so the main view can handle it
            raise e


class PrivacyView(TemplateView):
    template_name = 'core/privacy.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['page'] = Page.objects.get(page_type='privacy', is_published=True)
        except Page.DoesNotExist:
            context['page'] = None
        return context


class TermsView(TemplateView):
    template_name = 'core/terms.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['page'] = Page.objects.get(page_type='terms', is_published=True)
        except Page.DoesNotExist:
            context['page'] = None
        return context


class AdminLoginView(TemplateView):
    template_name = 'core/admin_login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Create a simple form context for the template
        context['form'] = {
            'username': '',
            'password': ''
        }
        return context
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return self.render_to_response(self.get_context_data())
        
        user = authenticate(username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('core:home')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')
            return self.render_to_response(self.get_context_data())


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/admin_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Staff privileges required.')
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get blog statistics
        context['total_posts'] = BlogPost.objects.count()
        context['published_posts'] = BlogPost.objects.filter(status='published').count()
        context['draft_posts'] = BlogPost.objects.filter(status='draft').count()
        context['featured_posts'] = BlogPost.objects.filter(is_featured=True).count()
        
        # Get recent posts
        context['recent_posts'] = BlogPost.objects.order_by('-created_at')[:5]
        
        # Get comment statistics
        from blog.models import Comment
        context['total_comments'] = Comment.objects.count()
        context['pending_comments'] = Comment.objects.filter(is_approved=False).count()
        context['recent_comments'] = Comment.objects.order_by('-created_at')[:5]
        
        # Get user statistics
        from django.contrib.auth.models import User
        context['total_users'] = User.objects.count()
        context['staff_users'] = User.objects.filter(is_staff=True).count()
        
        return context