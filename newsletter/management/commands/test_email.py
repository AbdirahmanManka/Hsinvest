from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

class Command(BaseCommand):
    help = 'Test email functionality for newsletter notifications'

    def handle(self, *args, **options):
        try:
            # Test email content
            subject = "Test Email - Newsletter System"
            
            html_content = """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">Newsletter System Test</h2>
                <p>This is a test email to verify that the newsletter notification system is working correctly.</p>
                
                <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1e40af; margin-top: 0;">Test Details:</h3>
                    <p><strong>From:</strong> Newsletter System</p>
                    <p><strong>To:</strong> {}</p>
                    <p><strong>Status:</strong> Email system is working!</p>
                </div>
                
                <p>If you receive this email, your newsletter notification system is properly configured.</p>
                
                <p style="color: #6b7280; font-size: 14px;">
                    This is a test email from your blog's newsletter system.
                </p>
            </div>
            """.format(settings.ADMIN_EMAIL)
            
            # Send test email
            send_mail(
                subject=subject,
                message=strip_tags(html_content),
                html_message=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=False,
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Test email sent successfully to {settings.ADMIN_EMAIL}!'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send test email: {str(e)}')
            )

