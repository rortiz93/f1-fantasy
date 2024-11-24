# management/commands/fetch_historical_standings.py
from django.core.management.base import BaseCommand
from league.utils import fetch_historical_standings_for_race
from league.models import Race

class Command(BaseCommand):
    help = "Fetch historical standings for a specific race"

    def add_arguments(self, parser):
        parser.add_argument(
            '--race-id',
            type=int,
            required=True,
            help='ID of the race to fetch historical standings for'
        )

    def handle(self, *args, **options):
        race_id = options['race_id']

        # Retrieve the race instance
        try:
            race = Race.objects.get(id=race_id)
        except Race.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Race with ID {race_id} does not exist."))
            return

        # Call the function to fetch historical standings
        fetch_historical_standings_for_race(race)
        self.stdout.write(self.style.SUCCESS(f"Historical standings fetched and updated for race: {race.template.name}"))