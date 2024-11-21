import os
import csv
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from league.models import Race, Team, Driver, TeamSelection

class Command(BaseCommand):
    help = 'Batch create TeamSelection instances from a CSV file for a specific team.'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help="Path to the CSV file.")
        parser.add_argument('team_name', type=str, help="Name of the team for which selections are being created.")

    @transaction.atomic
    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        team_name = kwargs['team_name']
        
        # Ensure the file exists
        if not os.path.exists(file_path):
            raise CommandError(f"File '{file_path}' does not exist.")

        # Run the batch creation function
        created_selections = batch_create_team_selections(file_path, team_name)
        
        # Provide feedback on the process
        if created_selections:
            self.stdout.write(self.style.SUCCESS(f"{len(created_selections)} team selections created for team '{team_name}'."))
        else:
            self.stdout.write(self.style.WARNING(f"No selections were created for team '{team_name}'."))

@transaction.atomic
def batch_create_team_selections(file_path, team_name):
    """
    Batch create TeamSelection instances from a CSV file for a given team.
    Each column represents a race, and each row below it represents drivers.
    """
    created_selections = []

    # Find the team object
    team = Team.objects.filter(name=team_name).first()
    if not team:
        print(f"Team not found: {team_name}")
        return []

    # Open and read the CSV file
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        race_names = reader.fieldnames  # Column names (race names)

        # For each race (column) in the CSV
        for race_name in race_names:
            # Get or create the race object
            race = Race.objects.filter(template__name=race_name).first()
            if not race:
                print(f"Race not found: {race_name}")
                continue

            # Reset file pointer to start to re-read driver rows for this race
            file.seek(0)
            next(reader)  # Skip the header row

            # Collect drivers for the current race
            driver_names = []
            for row in reader:
                driver_name = row[race_name]
                if driver_name:
                    driver_names.append(driver_name)

            # Find Driver objects based on names
            drivers = Driver.objects.filter(name__in=driver_names)
            if drivers.count() != len(driver_names):
                print(f"Some drivers not found for race {race_name}. Please check driver names.")
                continue

            # Create or get the team selection and set drivers
            team_selection, created = TeamSelection.objects.get_or_create(
                team=team,
                race=race,
                defaults={'points': Decimal('0.0')}
            )
            team_selection.drivers.set(drivers)
            team_selection.save()
            created_selections.append(team_selection)

    print(f"Batch creation complete. {len(created_selections)} team selections created.")
    return created_selections