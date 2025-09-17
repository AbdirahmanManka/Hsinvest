from .models import SiteConfiguration

def site_config(request):
    """Make site configuration available globally in templates"""
    try:
        site_config = SiteConfiguration.objects.first()
    except SiteConfiguration.DoesNotExist:
        site_config = None
    
    return {
        'site_config': site_config
    }
