from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            default=settings.ADMIN_EMAIL,
            help='Email address to send test email to (default: ADMIN_EMAIL from settings)'
        )

    def handle(self, *args, **options):
        recipient_email = options['to']
        
        self.stdout.write(
            self.style.SUCCESS(f'Testing email configuration...')
        )
        self.stdout.write(f'From: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'To: {recipient_email}')
        self.stdout.write(f'SMTP Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}')
        self.stdout.write(f'TLS Enabled: {settings.EMAIL_USE_TLS}')
        
        try:
            send_mail(
                subject='HasilInvest - Email Configuration Test',
                message='This is a test email from your HasilInvest Django application.\n\nIf you receive this email, your Gmail SMTP configuration is working correctly!\n\nBest regards,\nHasilInvest Team',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Test email sent successfully to {recipient_email}!')
            )
            self.stdout.write(
                self.style.SUCCESS('Email configuration is working properly.')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to send test email: {str(e)}')
            )
            self.stdout.write(
                self.style.ERROR('Please check your email configuration in .env file.')
            )
            
            # Provide troubleshooting tips
            self.stdout.write('\n' + self.style.WARNING('Troubleshooting tips:'))
            self.stdout.write('1. Verify your Gmail App Password is correct')
            self.stdout.write('2. Ensure 2-Factor Authentication is enabled on your Gmail account')
            self.stdout.write('3. Check that the Gmail account allows "Less secure app access" or use App Password')
            self.stdout.write('4. Verify your internet connection')
            self.stdout.write('5. Check if your firewall is blocking SMTP connections')
