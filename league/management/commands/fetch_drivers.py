import requests
from django.core.management.base import BaseCommand
from league.models import Driver

# API Endpoint
API_URL = "https://api.jolpi.ca/ergast/f1/{season}/drivers/"

class Command(BaseCommand):
    help = "Fetch the F1 drivers for a specific season and update/create Driver entries"

    def add_arguments(self, parser):
        # Optional season argument
        parser.add_argument(
            '--season',
            type=int,
            default=2024,  # Default season is 2024
            help='Season year to fetch driver data for'
        )

    def handle(self, *args, **options):
        season = options['season']
        url = API_URL.format(season=season)
        
        response = requests.get(url)
        if response.status_code != 200:
            self.stdout.write(self.style.ERROR(f"Failed to fetch data: {response.status_code}"))
            return
        
        data = response.json()
        drivers = data.get("MRData", {}).get("DriverTable", {}).get("Drivers", [])

        if not drivers:
            self.stdout.write(self.style.WARNING("No driver data found."))
            return

        created_count = 0
        updated_count = 0

        for driver_data in drivers:
            driver_id = driver_data.get("driverId")
            name = f"{driver_data['givenName']} {driver_data['familyName']}"
            nationality = driver_data.get("nationality")

            driver, created = Driver.objects.update_or_create(
                driver_id=driver_id,
                defaults={
                    "name": name,
                    "nationality": nationality,
                    "constructor": None,  # To be linked separately if constructor data is available
                    "tier": None,  # Can be updated later
                    "price": 1,  # Default price
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created driver: {driver.name}"))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"Updated driver: {driver.name}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully processed drivers for {season}: {created_count} created, {updated_count} updated."))