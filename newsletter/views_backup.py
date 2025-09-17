from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, ListView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import uuid
from .models import NewsletterSubscriber, EmailCampaign
from .services import NewsletterService

class SubscribeView(View):
    def post(self, request):
        try:
            # Get form data
            email = request.POST.get('email', '').strip().lower()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            frequency_preference = request.POST.get('frequency_preference', 'weekly')
            
            # Validate email
            if not email:
                return JsonResponse({'success': False, 'message': 'Email is required'})
            
            # Check if subscriber already exists
            if NewsletterSubscriber.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'This email is already subscribed'})
            
            # Create new subscriber
            subscriber = NewsletterSubscriber.objects.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                frequency_preference=frequency_preference,
                status='active',
                is_verified=True  # Auto-verify for now
            )
            
            # Send notification email to Habiba (admin)
            self.send_admin_notification(subscriber)
            
            # Send welcome email to subscriber
            self.send_welcome_email(subscriber)
            
            return JsonResponse({
                'success': True, 
                'message': f'Thank you for subscribing, {subscriber.get_full_name()}! You will receive our newsletter updates.'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.'})
    
    def send_admin_notification(self, subscriber):
        """Send notification email to admin when someone subscribes"""
        try:
            subject = f"New Newsletter Subscription - {subscriber.email}"
            
            # Create HTML email content
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">New Newsletter Subscription</h2>
                <p>Someone has subscribed to your newsletter!</p>
                
                <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1e40af; margin-top: 0;">Subscriber Details:</h3>
                    <p><strong>Name:</strong> {subscriber.get_full_name() or 'Not provided'}</p>
                    <p><strong>Email:</strong> {subscriber.email}</p>
                    <p><strong>Frequency:</strong> {subscriber.get_frequency_preference_display()}</p>
                    <p><strong>Subscription Date:</strong> {subscriber.subscribed_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <p>You can manage your subscribers at: <a href="{settings.SITE_URL}/newsletter/admin/subscribers/">Newsletter Dashboard</a></p>
                
                <p style="color: #6b7280; font-size: 14px;">
                    This is an automated notification from your blog's newsletter system.
                </p>
            </div>
            """
            
            # Send email to admin
            send_mail(
                subject=subject,
                message=strip_tags(html_content),
                html_message=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=False,
            )
            
        except Exception as e:
            print(f"Error sending admin notification: {e}")
    
    def send_welcome_email(self, subscriber):
        """Send welcome email to new subscriber"""
        try:
            subject = "Welcome to HasilInvest Newsletter!"
            
            # Create HTML email content
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">Welcome to HasilInvest!</h2>
                
                <p>Hi {subscriber.get_full_name() or 'there'},</p>
                
                <p>Thank you for subscribing to our newsletter! We're excited to have you join our community.</p>
                
                <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1e40af; margin-top: 0;">What to expect:</h3>
                    <ul style="color: #374151;">
                        <li>Latest blog posts and insights</li>
                        <li>Exclusive content and tips</li>
                        <li>Updates on halal investing and Islamic finance topics</li>
                        <li>Frequency: {subscriber.get_frequency_preference_display()}</li>
                    </ul>
                </div>
                
                <p>We promise to only send you valuable content and never spam your inbox.</p>
                
                <p>If you ever want to unsubscribe, you can do so at any time by clicking the unsubscribe link in any of our emails.</p>
                
                <p>Best regards,<br>
                <strong>HasilInvest Team</strong><br>
                HasilInvest: Halal Investing in Canada</p>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                <p style="color: #6b7280; font-size: 12px;">
                    You received this email because you subscribed to our newsletter at {settings.SITE_URL}.
                </p>
            </div>
            """
            
            # Send welcome email
            send_mail(
                subject=subject,
                message=strip_tags(html_content),
                html_message=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscriber.email],
                fail_silently=False,
            )
            
        except Exception as e:
            print(f"Error sending welcome email: {e}")

@method_decorator(staff_member_required, name='dispatch')
class BulkActionView(LoginRequiredMixin, View):
    """View for handling bulk actions on subscribers"""
    
    def post(self, request):
        action = request.POST.get('action')
        subscriber_ids = request.POST.getlist('subscriber_ids')
        
        if not subscriber_ids:
            messages.error(request, 'No subscribers selected')
            return redirect('newsletter:manage_subscribers')

@method_decorator(staff_member_required, name='dispatch')
class EditSubscriberView(LoginRequiredMixin, View):
    """View for editing a subscriber"""
    
    def get(self, request, subscriber_id):
        subscriber = get_object_or_404(NewsletterSubscriber, id=subscriber_id)
        from .models import Category
        
        # Get all available categories for interests
        categories = Category.objects.filter(is_active=True).order_by('name')
        
        context = {
            'subscriber': subscriber,
            'categories': categories,
        }
        return render(request, 'newsletter/edit_subscriber.html', context)
    
    def post(self, request, subscriber_id):
        from .models import Category
        
        try:
            subscriber = get_object_or_404(NewsletterSubscriber, id=subscriber_id)
            
            # Get form data
            subscriber.first_name = request.POST.get('first_name', '').strip()
            subscriber.last_name = request.POST.get('last_name', '').strip()
            subscriber.status = request.POST.get('status', 'active')
            subscriber.frequency_preference = request.POST.get('frequency_preference', 'weekly')
            subscriber.is_verified = request.POST.get('is_verified') == 'on'
            subscriber.country = request.POST.get('country', '').strip()
            subscriber.city = request.POST.get('city', '').strip()
            
            # Save the subscriber
            subscriber.save()
            
            # Update subscription interests
            subscription_interests = request.POST.getlist('subscription_interests')
            if subscription_interests:
                categories = Category.objects.filter(id__in=subscription_interests)
                subscriber.subscription_interests.set(categories)
            else:
                subscriber.subscription_interests.clear()
            
            messages.success(request, f'Subscriber "{subscriber.get_full_name()}" updated successfully!')
            return redirect('newsletter:manage_subscribers')
            
        except Exception as e:
            messages.error(request, f'Error updating subscriber: {str(e)}')
            return redirect('newsletter:edit_subscriber', subscriber_id=subscriber_id)
        
        try:
            subscribers = NewsletterSubscriber.objects.filter(id__in=subscriber_ids)
            
            if action == 'activate':
                count = subscribers.update(status='active')
                messages.success(request, f'Successfully activated {count} subscribers')
            elif action == 'unsubscribe':
                count = subscribers.update(status='unsubscribed')
                messages.success(request, f'Successfully unsubscribed {count} subscribers')
            elif action == 'delete':
                count = subscribers.count()
                subscribers.delete()
                messages.success(request, f'Successfully deleted {count} subscribers')
            else:
                messages.error(request, 'Invalid action')
                
        except Exception as e:
            messages.error(request, f'Error performing bulk action: {str(e)}')
        
        return redirect('newsletter:manage_subscribers')

@method_decorator(staff_member_required, name='dispatch')
class EditSubscriberView(LoginRequiredMixin, View):
    """View for editing a subscriber"""
    
    def get(self, request, subscriber_id):
        subscriber = get_object_or_404(NewsletterSubscriber, id=subscriber_id)
        from .models import Category
        
        # Get all available categories for interests
        categories = Category.objects.filter(is_active=True).order_by('name')
        
        context = {
            'subscriber': subscriber,
            'categories': categories,
        }
        return render(request, 'newsletter/edit_subscriber.html', context)
    
    def post(self, request, subscriber_id):
        from .models import Category
        
        try:
            subscriber = get_object_or_404(NewsletterSubscriber, id=subscriber_id)
            
            # Get form data
            subscriber.first_name = request.POST.get('first_name', '').strip()
            subscriber.last_name = request.POST.get('last_name', '').strip()
            subscriber.status = request.POST.get('status', 'active')
            subscriber.frequency_preference = request.POST.get('frequency_preference', 'weekly')
            subscriber.is_verified = request.POST.get('is_verified') == 'on'
            subscriber.country = request.POST.get('country', '').strip()
            subscriber.city = request.POST.get('city', '').strip()
            
            # Save the subscriber
            subscriber.save()
            
            # Update subscription interests
            subscription_interests = request.POST.getlist('subscription_interests')
            if subscription_interests:
                categories = Category.objects.filter(id__in=subscription_interests)
                subscriber.subscription_interests.set(categories)
            else:
                subscriber.subscription_interests.clear()
            
            messages.success(request, f'Subscriber "{subscriber.get_full_name()}" updated successfully!')
            return redirect('newsletter:manage_subscribers')
            
        except Exception as e:
            messages.error(request, f'Error updating subscriber: {str(e)}')
            return redirect('newsletter:edit_subscriber', subscriber_id=subscriber_id)

@method_decorator(staff_member_required, name='dispatch')
class UnsubscribeSubscriberView(LoginRequiredMixin, View):
    """View for unsubscribing a single subscriber"""
    
    def post(self, request, subscriber_id):
        try:
            subscriber = get_object_or_404(NewsletterSubscriber, id=subscriber_id)
            subscriber.status = 'unsubscribed'
            subscriber.save()
            messages.success(request, f'Successfully unsubscribed {subscriber.email}')
        except Exception as e:
            messages.error(request, f'Error unsubscribing subscriber: {str(e)}')
        
        return redirect('newsletter:manage_subscribers')

@method_decorator(staff_member_required, name='dispatch')
class EditSubscriberView(LoginRequiredMixin, View):
    """View for editing a subscriber"""
    
    def get(self, request, subscriber_id):
        subscriber = get_object_or_404(NewsletterSubscriber, id=subscriber_id)
        from .models import Category
        
        # Get all available categories for interests
        categories = Category.objects.filter(is_active=True).order_by('name')
        
        context = {
            'subscriber': subscriber,
            'categories': categories,
        }
        return render(request, 'newsletter/edit_subscriber.html', context)
    
    def post(self, request, subscriber_id):
        from .models import Category
        
        try:
            subscriber = get_object_or_404(NewsletterSubscriber, id=subscriber_id)
            
            # Get form data
            subscriber.first_name = request.POST.get('first_name', '').strip()
            subscriber.last_name = request.POST.get('last_name', '').strip()
            subscriber.status = request.POST.get('status', 'active')
            subscriber.frequency_preference = request.POST.get('frequency_preference', 'weekly')
            subscriber.is_verified = request.POST.get('is_verified') == 'on'
            subscriber.country = request.POST.get('country', '').strip()
            subscriber.city = request.POST.get('city', '').strip()
            
            # Save the subscriber
            subscriber.save()
            
            # Update subscription interests
            subscription_interests = request.POST.getlist('subscription_interests')
            if subscription_interests:
                categories = Category.objects.filter(id__in=subscription_interests)
                subscriber.subscription_interests.set(categories)
            else:
                subscriber.subscription_interests.clear()
            
            messages.success(request, f'Subscriber "{subscriber.get_full_name()}" updated successfully!')
            return redirect('newsletter:manage_subscribers')
            
        except Exception as e:
            messages.error(request, f'Error updating subscriber: {str(e)}')
            return redirect('newsletter:edit_subscriber', subscriber_id=subscriber_id)

class UnsubscribeView(View):
    def get(self, request, token):
        # Unsubscribe logic
        return render(request, 'newsletter/unsubscribe.html')

class ConfirmSubscriptionView(View):
    def get(self, request, token):
        # Confirmation logic
        return render(request, 'newsletter/confirm.html')

@method_decorator(staff_member_required, name='dispatch')
class NewsletterDashboardView(LoginRequiredMixin, ListView):
    """Admin dashboard for newsletter management"""
    model = EmailCampaign
    template_name = 'newsletter/admin_dashboard.html'
    context_object_name = 'campaigns'
    paginate_by = 10
    
    def get_queryset(self):
        return EmailCampaign.objects.all().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get subscriber statistics
        context['total_subscribers'] = NewsletterSubscriber.objects.filter(status='active').count()
        context['verified_subscribers'] = NewsletterSubscriber.objects.filter(
            status='active', is_verified=True
        ).count()
        context['recent_subscribers'] = NewsletterSubscriber.objects.filter(
            status='active'
        ).order_by('-subscribed_at')[:5]
        
        # Get campaign statistics
        context['total_campaigns'] = EmailCampaign.objects.count()
        context['sent_campaigns'] = EmailCampaign.objects.filter(status='sent').count()
        context['draft_campaigns'] = EmailCampaign.objects.filter(status='draft').count()
        
        return context

@method_decorator(staff_member_required, name='dispatch')
class SendNewsletterView(LoginRequiredMixin, View):
    """View for sending newsletters"""
    
    def post(self, request, campaign_id):
        campaign = get_object_or_404(EmailCampaign, id=campaign_id)
        
        if campaign.status != 'draft':
            messages.error(request, f'Campaign "{campaign.name}" is not in draft status')
            return redirect('newsletter:admin_dashboard')
        
        service = NewsletterService()
        result = service.send_campaign(campaign.id)
        
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['message'])
        
        return redirect('newsletter:admin_dashboard')
    
    def get(self, request, campaign_id):
        campaign = get_object_or_404(EmailCampaign, id=campaign_id)
        return render(request, 'newsletter/send_confirmation.html', {'campaign': campaign})

@method_decorator(staff_member_required, name='dispatch')
class SendTestEmailView(LoginRequiredMixin, View):
    """View for sending test emails"""
    
    def post(self, request, campaign_id):
        campaign = get_object_or_404(EmailCampaign, id=campaign_id)
        test_email = request.POST.get('test_email')
        
        if not test_email:
            messages.error(request, 'Please provide a test email address')
            return redirect('newsletter:admin_dashboard')
        
        service = NewsletterService()
        result = service.send_test_email(campaign.id, test_email)
        
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['message'])
        
        return redirect('newsletter:admin_dashboard')

@method_decorator(staff_member_required, name='dispatch')
class ManageSubscribersView(LoginRequiredMixin, ListView):
    """View for managing subscribers"""
    model = NewsletterSubscriber
    template_name = 'newsletter/manage_subscribers.html'
    context_object_name = 'subscribers'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = NewsletterSubscriber.objects.all().order_by('-subscribed_at')
        
        # Apply filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        verified = self.request.GET.get('verified')
        if verified == 'true':
            queryset = queryset.filter(is_verified=True)
        elif verified == 'false':
            queryset = queryset.filter(is_verified=False)
        
        frequency = self.request.GET.get('frequency')
        if frequency:
            queryset = queryset.filter(frequency_preference=frequency)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get subscriber statistics
        context['total_subscribers'] = NewsletterSubscriber.objects.count()
        context['active_subscribers'] = NewsletterSubscriber.objects.filter(status='active').count()
        context['unverified_subscribers'] = NewsletterSubscriber.objects.filter(is_verified=False).count()
        context['unsubscribed_count'] = NewsletterSubscriber.objects.filter(status='unsubscribed').count()
        
        return context

@method_decorator(staff_member_required, name='dispatch')
class CreateCampaignView(LoginRequiredMixin, View):
    """View for creating new campaigns"""
    
    def get(self, request):
        return render(request, 'newsletter/create_campaign.html')
    
    def post(self, request):
        from .models import EmailCampaign, Category
        
        # Get form data
        name = request.POST.get('name')
        campaign_type = request.POST.get('campaign_type')
        subject = request.POST.get('subject')
        preheader = request.POST.get('preheader')
        content = request.POST.get('content')
        plain_text_content = request.POST.get('plain_text_content')
        from_name = request.POST.get('from_name')
        from_email = request.POST.get('from_email')
        reply_to_email = request.POST.get('reply_to_email')
        send_to_all = request.POST.get('send_to_all') == 'on'
        target_categories = request.POST.getlist('target_categories')
        action = request.POST.get('action')
        
        # Create campaign
        campaign = EmailCampaign.objects.create(
            name=name,
            campaign_type=campaign_type,
            subject=subject,
            preheader=preheader,
            content=content,
            plain_text_content=plain_text_content,
            from_name=from_name,
            from_email=from_email,
            reply_to_email=reply_to_email,
            send_to_all=send_to_all,
            status='draft' if action == 'save_draft' else 'draft'
        )
        
        # Add target categories
        if target_categories:
            categories = Category.objects.filter(name__in=target_categories)
            campaign.target_categories.set(categories)
        
        messages.success(request, f'Campaign "{campaign.name}" created successfully!')
        
        if action == 'save_and_send':
            # Send the campaign
            service = NewsletterService()
            result = service.send_campaign(campaign.id)
            
            if result['success']:
                messages.success(request, f'Campaign sent to {result["sent_count"]} subscribers!')
            else:
                messages.error(request, f'Failed to send campaign: {result["message"]}')
        
        return redirect('newsletter:admin_dashboard')

@method_decorator(staff_member_required, name='dispatch')
class AddSubscriberView(LoginRequiredMixin, View):
    """View for adding new subscribers"""
    
    def get(self, request):
        return render(request, 'newsletter/add_subscriber.html')
    
    def post(self, request):
        from .models import NewsletterSubscriber, Category
        
        try:
            # Get form data
            email = request.POST.get('email', '').strip().lower()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            status = request.POST.get('status', 'active')
            frequency_preference = request.POST.get('frequency_preference', 'weekly')
            subscription_interests = request.POST.getlist('subscription_interests')
            is_verified = request.POST.get('is_verified') == 'on'
            send_welcome_email = request.POST.get('send_welcome_email') == 'on'
            ip_address = request.POST.get('ip_address', '')
            country = request.POST.get('country', '')
            city = request.POST.get('city', '')
            
            # Validate email
            if not email:
                return JsonResponse({'success': False, 'message': 'Email is required'})
            
            # Check if subscriber already exists
            if NewsletterSubscriber.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': f'A subscriber with email "{email}" already exists.'})
            
            # Create subscriber
            subscriber = NewsletterSubscriber.objects.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                status=status,
                frequency_preference=frequency_preference,
                is_verified=is_verified,
                ip_address=ip_address if ip_address else None,
                country=country,
                city=city
            )
            
            # Add subscription interests
            if subscription_interests:
                categories = Category.objects.filter(name__in=subscription_interests)
                subscriber.subscription_interests.set(categories)
            
            # Send welcome email if requested
            if send_welcome_email and is_verified:
                # Send welcome email
                self.send_welcome_email(subscriber)
            
            # Send admin notification
            self.send_admin_notification(subscriber)
            
            return JsonResponse({
                'success': True, 
                'message': f'Subscriber "{subscriber.get_full_name()}" added successfully!'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error adding subscriber: {str(e)}'})
    
    def send_admin_notification(self, subscriber):
        """Send notification email to admin when someone subscribes"""
        try:
            subject = f"New Newsletter Subscription - {subscriber.email}"
            
            # Create HTML email content
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">New Newsletter Subscription</h2>
                <p>Someone has subscribed to your newsletter!</p>
                
                <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1e40af; margin-top: 0;">Subscriber Details:</h3>
                    <p><strong>Name:</strong> {subscriber.get_full_name() or 'Not provided'}</p>
                    <p><strong>Email:</strong> {subscriber.email}</p>
                    <p><strong>Frequency:</strong> {subscriber.get_frequency_preference_display()}</p>
                    <p><strong>Subscription Date:</strong> {subscriber.subscribed_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <p>You can manage your subscribers at: <a href="{settings.SITE_URL}/newsletter/admin/subscribers/">Newsletter Dashboard</a></p>
                
                <p style="color: #6b7280; font-size: 14px;">
                    This is an automated notification from your blog's newsletter system.
                </p>
            </div>
            """
            
            # Send email to admin
            send_mail(
                subject=subject,
                message=strip_tags(html_content),
                html_message=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=False,
            )
            
        except Exception as e:
            print(f"Error sending admin notification: {e}")
    
    def send_welcome_email(self, subscriber):
        """Send welcome email to new subscriber"""
        try:
            subject = "Welcome to HasilInvest Newsletter!"
            
            # Create HTML email content
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">Welcome to HasilInvest!</h2>
                
                <p>Hi {subscriber.get_full_name() or 'there'},</p>
                
                <p>Thank you for subscribing to our newsletter! We're excited to have you join our community.</p>
                
                <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1e40af; margin-top: 0;">What to expect:</h3>
                    <ul style="color: #374151;">
                        <li>Latest blog posts and insights</li>
                        <li>Exclusive content and tips</li>
                        <li>Updates on halal investing and Islamic finance topics</li>
                        <li>Frequency: {subscriber.get_frequency_preference_display()}</li>
                    </ul>
                </div>
                
                <p>We promise to only send you valuable content and never spam your inbox.</p>
                
                <p>If you ever want to unsubscribe, you can do so at any time by clicking the unsubscribe link in any of our emails.</p>
                
                <p>Best regards,<br>
                <strong>HasilInvest Team</strong><br>
                HasilInvest: Halal Investing in Canada</p>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                <p style="color: #6b7280; font-size: 12px;">
                    You received this email because you subscribed to our newsletter at {settings.SITE_URL}.
                </p>
            </div>
            """
            
            # Send welcome email
            send_mail(
                subject=subject,
                message=strip_tags(html_content),
                html_message=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscriber.email],
                fail_silently=False,
            )
            
        except Exception as e:
            print(f"Error sending welcome email: {e}")

@method_decorator(staff_member_required, name='dispatch')
class BulkActionView(LoginRequiredMixin, View):
    """View for handling bulk actions on subscribers"""
    
    def post(self, request):
        action = request.POST.get('action')
        subscriber_ids = request.POST.getlist('subscriber_ids')
        
        if not subscriber_ids:
            messages.error(request, 'No subscribers selected')
            return redirect('newsletter:manage_subscribers')

@method_decorator(staff_member_required, name='dispatch')
class EditSubscriberView(LoginRequiredMixin, View):
    """View for editing a subscriber"""
    
    def get(self, request, subscriber_id):
        subscriber = get_object_or_404(NewsletterSubscriber, id=subscriber_id)
        from .models import Category
        
        # Get all available categories for interests
        categories = Category.objects.filter(is_active=True).order_by('name')
        
        context = {
            'subscriber': subscriber,
            'categories': categories,
        }
        return render(request, 'newsletter/edit_subscriber.html', context)
    
    def post(self, request, subscriber_id):
        from .models import Category
        
        try:
            subscriber = get_object_or_404(NewsletterSubscriber, id=subscriber_id)
            
            # Get form data
            subscriber.first_name = request.POST.get('first_name', '').strip()
            subscriber.last_name = request.POST.get('last_name', '').strip()
            subscriber.status = request.POST.get('status', 'active')
            subscriber.frequency_preference = request.POST.get('frequency_preference', 'weekly')
            subscriber.is_verified = request.POST.get('is_verified') == 'on'
            subscriber.country = request.POST.get('country', '').strip()
            subscriber.city = request.POST.get('city', '').strip()
            
            # Save the subscriber
            subscriber.save()
            
            # Update subscription interests
            subscription_interests = request.POST.getlist('subscription_interests')
            if subscription_interests:
                categories = Category.objects.filter(id__in=subscription_interests)
                subscriber.subscription_interests.set(categories)
            else:
                subscriber.subscription_interests.clear()
            
            messages.success(request, f'Subscriber "{subscriber.get_full_name()}" updated successfully!')
            return redirect('newsletter:manage_subscribers')
            
        except Exception as e:
            messages.error(request, f'Error updating subscriber: {str(e)}')
            return redirect('newsletter:edit_subscriber', subscriber_id=subscriber_id)
        
        try:
            subscribers = NewsletterSubscriber.objects.filter(id__in=subscriber_ids)
            
            if action == 'activate':
                count = subscribers.update(status='active')
                messages.success(request, f'Successfully activated {count} subscribers')
            elif action == 'unsubscribe':
                count = subscribers.update(status='unsubscribed')
                messages.success(request, f'Successfully unsubscribed {count} subscribers')
            elif action == 'delete':
                count = subscribers.count()
                subscribers.delete()
                messages.success(request, f'Successfully deleted {count} subscribers')
            else:
                messages.error(request, 'Invalid action')
                
        except Exception as e:
            messages.error(request, f'Error performing bulk action: {str(e)}')
        
        return redirect('newsletter:manage_subscribers')

@method_decorator(staff_member_required, name='dispatch')
class EditSubscriberView(LoginRequiredMixin, View):
    """View for editing a subscriber"""
    
    def get(self, request, subscriber_id):
        subscriber = get_object_or_404(NewsletterSubscriber, id=subscriber_id)
        from .models import Category
        
        # Get all available categories for interests
        categories = Category.objects.filter(is_active=True).order_by('name')
        
        context = {
            'subscriber': subscriber,
            'categories': categories,
        }
        return render(request, 'newsletter/edit_subscriber.html', context)
    
    def post(self, request, subscriber_id):
        from .models import Category
        
        try:
            subscriber = get_object_or_404(NewsletterSubscriber, id=subscriber_id)
            
            # Get form data
            subscriber.first_name = request.POST.get('first_name', '').strip()
            subscriber.last_name = request.POST.get('last_name', '').strip()
            subscriber.status = request.POST.get('status', 'active')
            subscriber.frequency_preference = request.POST.get('frequency_preference', 'weekly')
            subscriber.is_verified = request.POST.get('is_verified') == 'on'
            subscriber.country = request.POST.get('country', '').strip()
            subscriber.city = request.POST.get('city', '').strip()
            
            # Save the subscriber
            subscriber.save()
            
            # Update subscription interests
            subscription_interests = request.POST.getlist('subscription_interests')
            if subscription_interests:
                categories = Category.objects.filter(id__in=subscription_interests)
                subscriber.subscription_interests.set(categories)
            else:
                subscriber.subscription_interests.clear()
            
            messages.success(request, f'Subscriber "{subscriber.get_full_name()}" updated successfully!')
            return redirect('newsletter:manage_subscribers')
            
        except Exception as e:
            messages.error(request, f'Error updating subscriber: {str(e)}')
            return redirect('newsletter:edit_subscriber', subscriber_id=subscriber_id)

@method_decorator(staff_member_required, name='dispatch')
class UnsubscribeSubscriberView(LoginRequiredMixin, View):
    """View for unsubscribing a single subscriber"""
    
    def post(self, request, subscriber_id):
        try:
            subscriber = get_object_or_404(NewsletterSubscriber, id=subscriber_id)
            subscriber.status = 'unsubscribed'
            subscriber.save()
            messages.success(request, f'Successfully unsubscribed {subscriber.email}')
        except Exception as e:
            messages.error(request, f'Error unsubscribing subscriber: {str(e)}')
        
        return redirect('newsletter:manage_subscribers')

@method_decorator(staff_member_required, name='dispatch')
class EditSubscriberView(LoginRequiredMixin, View):
    """View for editing a subscriber"""
    
    def get(self, request, subscriber_id):
        subscriber = get_object_or_404(NewsletterSubscriber, id=subscriber_id)
        from .models import Category
        
        # Get all available categories for interests
        categories = Category.objects.filter(is_active=True).order_by('name')
        
        context = {
            'subscriber': subscriber,
            'categories': categories,
        }
        return render(request, 'newsletter/edit_subscriber.html', context)
    
    def post(self, request, subscriber_id):
        from .models import Category
        
        try:
            subscriber = get_object_or_404(NewsletterSubscriber, id=subscriber_id)
            
            # Get form data
            subscriber.first_name = request.POST.get('first_name', '').strip()
            subscriber.last_name = request.POST.get('last_name', '').strip()
            subscriber.status = request.POST.get('status', 'active')
            subscriber.frequency_preference = request.POST.get('frequency_preference', 'weekly')
            subscriber.is_verified = request.POST.get('is_verified') == 'on'
            subscriber.country = request.POST.get('country', '').strip()
            subscriber.city = request.POST.get('city', '').strip()
            
            # Save the subscriber
            subscriber.save()
            
            # Update subscription interests
            subscription_interests = request.POST.getlist('subscription_interests')
            if subscription_interests:
                categories = Category.objects.filter(id__in=subscription_interests)
                subscriber.subscription_interests.set(categories)
            else:
                subscriber.subscription_interests.clear()
            
            messages.success(request, f'Subscriber "{subscriber.get_full_name()}" updated successfully!')
            return redirect('newsletter:manage_subscribers')
            
        except Exception as e:
            messages.error(request, f'Error updating subscriber: {str(e)}')
            return redirect('newsletter:edit_subscriber', subscriber_id=subscriber_id)