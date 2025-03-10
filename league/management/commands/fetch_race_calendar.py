import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from league.models import RaceTemplate

# Updated API endpoint
API_URL = "https://api.jolpi.ca/ergast/f1/{season}/races/"

class Command(BaseCommand):
    help = "Fetch the F1 race calendar for a specific season and update/create RaceTemplate entries"

    def add_arguments(self, parser):
        # Optional season argument
        parser.add_argument(
            '--season',
            type=int,
            default=2025,  # Default season is 2025
            help='Season year to fetch the race calendar for'
        )

    def handle(self, *args, **options):
        season = options['season']
        url = API_URL.format(season=season)
        
        response = requests.get(url)
        if response.status_code != 200:
            self.stdout.write(self.style.ERROR(f"Failed to fetch data: {response.status_code}"))
            return
        
        data = response.json()
        races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])

        if not races:
            self.stdout.write(self.style.WARNING("No race data found."))
            return

        created_count = 0
        updated_count = 0

        for race_data in races:
            round_number = int(race_data["round"])
            name = race_data["raceName"]
            date = race_data["date"]
            circuit = race_data["Circuit"]["circuitName"]
            location = f"{race_data['Circuit']['Location']['locality']}, {race_data['Circuit']['Location']['country']}"

             # Parse Qualifying start time
            qualifying_start_time = None
            qualifying_data = race_data.get("Qualifying")
            if qualifying_data:
                qualifying_date = qualifying_data.get("date")
                qualifying_time = qualifying_data.get("time")
                if qualifying_date and qualifying_time:
                    qualifying_start_time = datetime.strptime(
                        f"{qualifying_date}T{qualifying_time}", "%Y-%m-%dT%H:%M:%SZ"
                    )

            # Parse First Practice start time
            first_practice_start_time = None
            practice_data = race_data.get("FirstPractice")
            if practice_data:
                practice_date = practice_data.get("date")
                practice_time = practice_data.get("time")
                if practice_date and practice_time:
                    first_practice_start_time = datetime.strptime(
                        f"{practice_date}T{practice_time}", "%Y-%m-%dT%H:%M:%SZ"
                    )

            race, created = RaceTemplate.objects.update_or_create(
                season=season,
                round=round_number,
                defaults={
                    "name": name,
                    "date": date,
                    "location": location,
                    "circuit": circuit,
                    "qualifying_start_time": qualifying_start_time,
                    "first_practice_start_time": first_practice_start_time,
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created race: {race.name}"))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"Updated race: {race.name}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully processed race calendar for {season}: {created_count} created, {updated_count} updated."))