
import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from league.models import RaceTemplate, League, Race 
class Command(BaseCommand):
    def handle(self, *args, **options):
        league = League.objects.get(name="RCFORL")  # Get a specific league
        race_templates = RaceTemplate.objects.filter(season=2025)  # Filter templates for the season

        # Create a Race instance in the league for each template
        for template in race_templates:
            # Lineup deadline is 12 hours before first practice start time
            lineup_deadline = template.first_practice_start_time - timedelta(hours=12)
            # Mulligan deadline is 1 hour before qualifying start time
            mulligan_deadline = template.qualifying_start_time - timedelta(hours=1)
            Race.objects.create(
                template=template,
                league=league,
                lineup_deadline=lineup_deadline,
                mulligan_deadline=mulligan_deadline
            )