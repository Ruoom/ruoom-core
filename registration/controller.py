from administration.models import StudioSettings, DomainToBusinessMapping
from administration.management.commands import create_view_groups
from django.conf import settings
import chargebee

# This function is used to return the business id for the domain. Useful when app is deployed to multiple URLs against the same database
def return_business_id_for_domain(request_domain):

    if not StudioSettings.objects.filter(business_id=1).exists():
        StudioSettings.objects.create(business_id=1, name="ruoom_default")

        #Also create user groups since this is the first data in the db
        create_view_groups.Command.handle(0)
        
    for url in settings.LOCAL_URLS:
        if request_domain in url or url in request_domain:
            return 1

    try: #try to import domain to business mapping
        from administration.models import DomainToBusinessMapping

        mappings = DomainToBusinessMapping.objects.all()
        for mapping in mappings:
            if request_domain in mapping.domain:
                return mapping.business.business_id
        
        return 1
    except ImportError:
        return 1