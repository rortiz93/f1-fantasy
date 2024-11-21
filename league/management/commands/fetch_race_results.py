# management/commands/fetch_driver_race_results.py
from django.core.management.base import BaseCommand
from league.utils import fetch_driver_race_results, populate_historical_standings_for_all_races

class Command(BaseCommand):
    help = "Fetch driver race results for a specific season"

    def add_arguments(self, parser):
        parser.add_argument('--season', type=int, default=2024, help='Season year to fetch race results for')

    def handle(self, *args, **options):
        season = options['season']
        message = populate_historical_standings_for_all_races()
        self.stdout.write(self.style.SUCCESS(message))