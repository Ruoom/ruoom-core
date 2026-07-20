from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from administration.domain_bootstrap import normalize_domain
from administration.models import Business, DomainToBusinessMapping


class Command(BaseCommand):
    help = (
        "Register RUOOM_BUSINESS_1_URL for business 1. "
        "The command is safe to run after every deployment."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            default="",
            help="Override RUOOM_BUSINESS_1_URL for this invocation.",
        )

    def handle(self, *args, **options):
        configured_url = (options["url"] or settings.RUOOM_BUSINESS_1_URL).strip()
        if not configured_url:
            self.stdout.write("RUOOM_BUSINESS_1_URL is not configured; skipping.")
            return

        domain = normalize_domain(configured_url)
        if not domain:
            raise CommandError(
                "RUOOM_BUSINESS_1_URL must contain a valid hostname or URL."
            )

        with transaction.atomic():
            business, created = Business.objects.get_or_create(
                business_id=1,
                defaults={"name": "ruoom_default"},
            )

            conflicting_mapping = next(
                (
                    mapping
                    for mapping in DomainToBusinessMapping.objects.select_related("business")
                    if normalize_domain(mapping.domain) == domain
                    and mapping.business_id != business.pk
                ),
                None,
            )
            if conflicting_mapping:
                raise CommandError(
                    f"The domain '{domain}' is already assigned to "
                    f"business {conflicting_mapping.business.business_id}."
                )

            mapping, mapping_created = DomainToBusinessMapping.objects.update_or_create(
                business=business,
                defaults={"domain": domain},
            )

            if created:
                call_command("create_view_groups", verbosity=0)

        action = "Registered" if mapping_created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} business 1 domain mapping: {mapping.domain}"
            )
        )
