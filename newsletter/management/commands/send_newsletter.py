from django.core.management.base import BaseCommand, CommandError
from newsletter.models import EmailCampaign
from newsletter.services import NewsletterService


class Command(BaseCommand):
    help = 'Send newsletter campaigns to subscribers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--campaign-id',
            type=int,
            help='ID of the campaign to send',
        )
        parser.add_argument(
            '--campaign-name',
            type=str,
            help='Name of the campaign to send',
        )
        parser.add_argument(
            '--test-email',
            type=str,
            help='Send test email to this address instead of all subscribers',
        )
        parser.add_argument(
            '--list-campaigns',
            action='store_true',
            help='List all available campaigns',
        )

    def handle(self, *args, **options):
        service = NewsletterService()

        # List campaigns
        if options['list_campaigns']:
            self.list_campaigns()
            return

        # Get campaign
        campaign = None
        if options['campaign_id']:
            try:
                campaign = EmailCampaign.objects.get(id=options['campaign_id'])
            except EmailCampaign.DoesNotExist:
                raise CommandError(f'Campaign with ID {options["campaign_id"]} does not exist')
        elif options['campaign_name']:
            try:
                campaign = EmailCampaign.objects.get(name=options['campaign_name'])
            except EmailCampaign.DoesNotExist:
                raise CommandError(f'Campaign with name "{options["campaign_name"]}" does not exist')
        else:
            raise CommandError('Please specify either --campaign-id or --campaign-name')

        # Send test email
        if options['test_email']:
            result = service.send_test_email(campaign.id, options['test_email'])
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(result['message'])
                )
            else:
                raise CommandError(result['message'])
            return

        # Send campaign
        if campaign.status != 'draft':
            raise CommandError(f'Campaign "{campaign.name}" is not in draft status (current: {campaign.get_status_display()})')

        self.stdout.write(f'Sending campaign: {campaign.name}')
        self.stdout.write(f'Subject: {campaign.subject}')
        
        result = service.send_campaign(campaign.id)
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(f'✅ {result["message"]}')
            )
            self.stdout.write(f'📊 Sent: {result["sent_count"]}/{result["total_recipients"]} emails')
        else:
            raise CommandError(f'❌ {result["message"]}')

    def list_campaigns(self):
        """List all available campaigns"""
        campaigns = EmailCampaign.objects.all().order_by('-created_at')
        
        if not campaigns.exists():
            self.stdout.write(self.style.WARNING('No campaigns found'))
            return

        self.stdout.write(self.style.SUCCESS('Available Campaigns:'))
        self.stdout.write('-' * 80)
        
        for campaign in campaigns:
            status_color = {
                'draft': 'yellow',
                'scheduled': 'blue',
                'sending': 'orange',
                'sent': 'green',
                'paused': 'orange',
                'cancelled': 'red'
            }.get(campaign.status, 'white')
            
            status_style = getattr(self.style, status_color.upper(), self.style.SUCCESS)
            
            self.stdout.write(f'ID: {campaign.id} | Name: {campaign.name}')
            self.stdout.write(f'    Status: {status_style(campaign.get_status_display())}')
            self.stdout.write(f'    Subject: {campaign.subject}')
            self.stdout.write(f'    Type: {campaign.get_campaign_type_display()}')
            self.stdout.write(f'    Created: {campaign.created_at.strftime("%Y-%m-%d %H:%M")}')
            if campaign.sent_at:
                self.stdout.write(f'    Sent: {campaign.sent_at.strftime("%Y-%m-%d %H:%M")}')
            self.stdout.write('-' * 80)
