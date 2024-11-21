from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Min
from league.models import Race, League

class Command(BaseCommand):
    help = 'Deletes duplicate Race entries within each League, keeping only the first occurrence based on the template.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting to delete duplicate races within each league..."))

        with transaction.atomic():
            # Find duplicates in Race based on League and Template
            duplicates = (
                Race.objects
                .values('league', 'template')  # Group by league and template
                .annotate(min_id=Min('id'))    # Get the earliest entry ID for each duplicate group
                .order_by()
            )

            # Collect IDs of all non-duplicate entries to keep
            ids_to_keep = {entry['min_id'] for entry in duplicates}

            # Delete duplicates excluding those in ids_to_keep
            deleted_count, _ = Race.objects.exclude(id__in=ids_to_keep).delete()

            self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} duplicate races."))