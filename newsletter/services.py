from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from .models import EmailCampaign, NewsletterSubscriber, NewsletterActivity
import logging

logger = logging.getLogger(__name__)


class NewsletterService:
    """Service for sending newsletters and managing email campaigns"""
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
        self.from_name = "HasilInvest"
    
    def send_campaign(self, campaign_id):
        """Send an email campaign to all targeted subscribers"""
        try:
            campaign = EmailCampaign.objects.get(id=campaign_id)
            
            if campaign.status != 'draft':
                raise ValueError(f"Campaign {campaign.name} is not in draft status")
            
            # Get target subscribers
            subscribers = self._get_target_subscribers(campaign)
            
            if not subscribers.exists():
                raise ValueError("No subscribers found for this campaign")
            
            # Update campaign status
            campaign.status = 'sending'
            campaign.total_recipients = subscribers.count()
            campaign.save()
            
            # Send emails
            sent_count = 0
            for subscriber in subscribers:
                try:
                    self._send_email_to_subscriber(campaign, subscriber)
                    sent_count += 1
                    
                    # Update subscriber metrics
                    subscriber.total_emails_sent += 1
                    subscriber.save()
                    
                except Exception as e:
                    logger.error(f"Failed to send email to {subscriber.email}: {str(e)}")
                    continue
            
            # Update campaign status
            campaign.status = 'sent'
            campaign.total_sent = sent_count
            campaign.sent_at = timezone.now()
            campaign.save()
            
            return {
                'success': True,
                'message': f'Campaign sent to {sent_count} subscribers',
                'sent_count': sent_count,
                'total_recipients': campaign.total_recipients
            }
            
        except EmailCampaign.DoesNotExist:
            return {'success': False, 'message': 'Campaign not found'}
        except Exception as e:
            logger.error(f"Error sending campaign {campaign_id}: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def send_test_email(self, campaign_id, test_email):
        """Send a test email for a campaign"""
        try:
            campaign = EmailCampaign.objects.get(id=campaign_id)
            
            # Create a temporary subscriber for testing
            test_subscriber = NewsletterSubscriber(
                email=test_email,
                first_name="Test",
                last_name="User"
            )
            
            self._send_email_to_subscriber(campaign, test_subscriber)
            
            return {
                'success': True,
                'message': f'Test email sent to {test_email}'
            }
            
        except EmailCampaign.DoesNotExist:
            return {'success': False, 'message': 'Campaign not found'}
        except Exception as e:
            logger.error(f"Error sending test email: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def _get_target_subscribers(self, campaign):
        """Get the list of subscribers to target for a campaign"""
        subscribers = NewsletterSubscriber.objects.filter(
            status='active',
            is_verified=True
        )
        
        if not campaign.send_to_all:
            if campaign.target_categories.exists():
                # Filter by category interests
                subscribers = subscribers.filter(
                    subscription_interests__in=campaign.target_categories.all()
                ).distinct()
            
            if campaign.target_subscribers.exists():
                # Filter by specific subscribers
                subscribers = subscribers.filter(
                    id__in=campaign.target_subscribers.values_list('id', flat=True)
                )
        
        return subscribers
    
    def _send_email_to_subscriber(self, campaign, subscriber):
        """Send email to a specific subscriber"""
        try:
            # Prepare email content
            subject = campaign.subject
            html_content = self._render_email_content(campaign, subscriber)
            plain_content = campaign.plain_text_content or self._strip_html(html_content)
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_content,
                from_email=f"{campaign.from_name or 'HasilInvest'} <{campaign.from_email or self.from_email}>",
                to=[subscriber.email],
                reply_to=[campaign.reply_to_email] if campaign.reply_to_email else None
            )
            
            # Attach HTML version
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            
            # Log activity
            NewsletterActivity.objects.create(
                subscriber=subscriber,
                campaign=campaign,
                activity_type='email_sent',
                email_subject=subject,
                description=f"Email sent for campaign: {campaign.name}"
            )
            
        except Exception as e:
            logger.error(f"Failed to send email to {subscriber.email}: {str(e)}")
            raise
    
    def _render_email_content(self, campaign, subscriber):
        """Render email content with subscriber-specific data"""
        context = {
            'subscriber': subscriber,
            'campaign': campaign,
            'unsubscribe_url': subscriber.get_unsubscribe_url(),
            'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
        }
        
        # Use a simple template for now
        template_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{campaign.subject}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                .unsubscribe {{ margin-top: 20px; }}
                .unsubscribe a {{ color: #666; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>HasilInvest Newsletter</h1>
                </div>
                <div class="content">
                    <h2>Hello {subscriber.get_full_name()}!</h2>
                    {campaign.content}
                </div>
                <div class="footer">
                    <p>You received this email because you subscribed to HasilInvest newsletter.</p>
                    <div class="unsubscribe">
                        <a href="{subscriber.get_unsubscribe_url()}">Unsubscribe</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return template_content
    
    def _strip_html(self, html_content):
        """Convert HTML content to plain text"""
        import re
        # Remove HTML tags
        plain_text = re.sub('<[^<]+?>', '', html_content)
        # Clean up whitespace
        plain_text = re.sub(r'\s+', ' ', plain_text).strip()
        return plain_text
    
    def get_campaign_stats(self, campaign_id):
        """Get statistics for a campaign"""
        try:
            campaign = EmailCampaign.objects.get(id=campaign_id)
            
            return {
                'campaign_name': campaign.name,
                'status': campaign.get_status_display(),
                'total_recipients': campaign.total_recipients,
                'total_sent': campaign.total_sent,
                'total_delivered': campaign.total_delivered,
                'total_opened': campaign.total_opened,
                'total_clicked': campaign.total_clicked,
                'open_rate': campaign.get_open_rate(),
                'click_rate': campaign.get_click_rate(),
                'delivery_rate': campaign.get_delivery_rate(),
                'created_at': campaign.created_at,
                'sent_at': campaign.sent_at,
            }
            
        except EmailCampaign.DoesNotExist:
            return None
