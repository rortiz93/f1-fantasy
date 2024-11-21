import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from league.models import RaceTemplate

# Define your API URL
API_URL = "http://ergast.com/api/f1/{season}.json"

class Command(BaseCommand):
    help = "Fetch the F1 race calendar for a specific season"

    def add_arguments(self, parser):
        # Optional season argument
        parser.add_argument(
            '--season',
            type=int,
            default=2024,  # Set a default season if none is provided
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
        races = data['MRData']['RaceTable']['Races']

        for race_data in races:
            # Parse qualifying date and time to set the lineup deadline
            qualifying_date = race_data['Qualifying']['date']
            qualifying_time = race_data['Qualifying']['time']
            
            if qualifying_date and qualifying_time:
                # Combine date and time, and subtract 3 hours for the lineup deadline
                qualifying_datetime = datetime.strptime(f"{qualifying_date}T{qualifying_time}", "%Y-%m-%dT%H:%M:%SZ")
                lineup_deadline_real = qualifying_datetime - timedelta(hours=3)
            race, created = RaceTemplate.objects.update_or_create(
                name=race_data['raceName'],
                date=race_data['date'],
                defaults={
                  
                    'location': race_data['Circuit']['Location']['locality'],
                    'season': race_data['season'],
                    'round': race_data['round'],
                    'circuit': race_data['Circuit']['circuitName'],
                    
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created race: {race.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated race: {race.name}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully fetched race calendar for {season}"))