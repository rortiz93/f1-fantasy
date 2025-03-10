import requests
from django.core.management.base import BaseCommand
from league.models import Constructor

# API Endpoint
API_URL = "https://api.jolpi.ca/ergast/f1/{season}/constructors/"

class Command(BaseCommand):
    help = "Fetch the F1 constructors for a specific season and update/create Constructor entries"

    def add_arguments(self, parser):
        # Optional season argument
        parser.add_argument(
            '--season',
            type=int,
            default=2025,  # Default season is 2025
            help='Season year to fetch constructor data for'
        )

    def handle(self, *args, **options):
        season = options['season']
        url = API_URL.format(season=season)
        
        response = requests.get(url)
        if response.status_code != 200:
            self.stdout.write(self.style.ERROR(f"Failed to fetch data: {response.status_code}"))
            return
        
        data = response.json()
        constructors = data.get("MRData", {}).get("ConstructorTable", {}).get("Constructors", [])

        if not constructors:
            self.stdout.write(self.style.WARNING("No constructor data found."))
            return

        created_count = 0
        updated_count = 0

        for constructor_data in constructors:
            name = constructor_data["name"]

            constructor, created = Constructor.objects.update_or_create(
                name=name,
                defaults={
                    "standing": None,  # Standing not provided in the API, can be updated later
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created constructor: {constructor.name}"))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"Updated constructor: {constructor.name}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully processed constructors for {season}: {created_count} created, {updated_count} updated."))