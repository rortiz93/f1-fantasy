# management/commands/fetch_driver_race_results.py
from django.core.management.base import BaseCommand
from league.models import Race
from league.utils import fetch_session_results

class Command(BaseCommand):
    help = "Fetch session results for a specific race and session type"

    def add_arguments(self, parser):
        parser.add_argument('--race-id', type=int, required=True, help='ID of the race to fetch results for')
        parser.add_argument('--session-type', type=str, required=True, choices=['Qualifying', 'Sprint', 'Race'],
                            help='Session type to fetch results for (Qualifying, Sprint, or Race)')

    def handle(self, *args, **options):
        race_id = options['race_id']
        session_type = options['session_type']

        try:
            race = Race.objects.get(pk=race_id)
            fetch_session_results(race, session_type)
            self.stdout.write(self.style.SUCCESS(
                f"Successfully fetched {session_type} results for race ID {race_id}."
            ))
        except Race.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Race with ID {race_id} does not exist."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {str(e)}"))