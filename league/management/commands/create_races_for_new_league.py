
import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from league.models import RaceTemplate, League, Race 
class Command(BaseCommand):
    def handle(self, *args, **options):
        league = League.objects.get(name="RCFORL")  # Get a specific league
        race_templates = RaceTemplate.objects.filter(season=2024)  # Filter templates for the season

        # Create a Race instance in the league for each template
        for template in race_templates:
            Race.objects.create(template=template, league=league, lineup_deadline=template.date - timedelta(days=3))