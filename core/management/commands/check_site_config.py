from django.core.management.base import BaseCommand
from core.models import SiteConfiguration

class Command(BaseCommand):
    help = 'Check and create SiteConfiguration if needed'

    def handle(self, *args, **options):
        config_count = SiteConfiguration.objects.count()
        self.stdout.write(f'SiteConfiguration count: {config_count}')
        
        if config_count == 0:
            self.stdout.write('Creating SiteConfiguration...')
            config = SiteConfiguration.objects.create(
                site_name="Habiba's Blog",
                site_description=(
                    "A platform to make investing and personal finance easy to understand "
                    "for everyone — open to anyone who wants to grow wealth responsibly. "
                    "Ethically driven, with guidance for halal‑conscious investors."
                ),
                site_keywords=(
                    "personal finance, investing, ethical investing, halal investing, "
                    "responsible wealth, budgeting, saving, portfolio basics"
                ),
                email="hasilinvestt@gmail.com",
                meta_description=(
                    "Clear, inclusive guidance on personal finance and responsible investing, "
                    "with additional support for halal‑conscious strategies."
                )
            )
            self.stdout.write('SiteConfiguration created successfully!')
        else:
            config = SiteConfiguration.objects.first()
            
        self.stdout.write(f'Facebook URL: {config.facebook_url}')
        self.stdout.write(f'Twitter URL: {config.twitter_url}')
        self.stdout.write(f'LinkedIn URL: {config.linkedin_url}')
