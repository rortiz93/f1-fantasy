
from collections import defaultdict
from django.utils import timezone
from decimal import Decimal
from .models import TeamSelection, RaceResult, Driver, Constructor, RaceTemplate, Race, HistoricalConstructorStanding,PredictionAnswer

from decimal import Decimal

FIA_POINTS = {1: Decimal('25.0'), 2: Decimal('18.0'), 3: Decimal('15.0'), 4: Decimal('12.0'), 5: Decimal('10.0'),
              6: Decimal('8.0'), 7: Decimal('6.0'), 8: Decimal('4.0'), 9: Decimal('2.0'), 10: Decimal('1.0')}
FIA_POINTS_SPRINT = {1: Decimal('8.0'), 2: Decimal('7.0'), 3: Decimal('6.0'), 4: Decimal('5.0'), 5: Decimal('4.0'),
                     6: Decimal('3.0'), 7: Decimal('2.0'), 8: Decimal('1.0')}

def get_base_points(position, session_type):
    points_dict = FIA_POINTS_SPRINT if session_type == 'Sprint' else FIA_POINTS
    return points_dict.get(position, Decimal('0.0'))

def adjust_points_by_tier(driver, base_points, session_type, result, race=None):
    session_points = base_points
    is_tier_override = False
    if result and hasattr(result, 'is_tier_override') and result.is_tier_override:
        is_tier_override = True
          # Debugging: Print information about the override
        
   
    if driver.tier == 2 and not is_tier_override:
        session_points *= Decimal('2.5')
        
        # Apply bonus points if race is available, it's a Race session, and other conditions are met
        if session_type == 'Race' and race and race.template and race.template.round > 3:
            # Determine the previous race based on the current race's round
            previous_race = Race.objects.filter(
                league=race.league,
                template__round=race.template.round - 1
            ).first()

            if previous_race:
                # Retrieve historical standings for the constructor at the previous race
                historical_standing = HistoricalConstructorStanding.objects.filter(
                    race=previous_race, constructor=driver.constructor
                ).first()

                # Check if the result position qualifies for the bonus points
                if (
                    historical_standing and historical_standing.standing >= 8 and
                    result.position <= 15  # Using the specific result instance for position check
                ):
                    session_points += Decimal('4.0')  # Add bonus points
    return session_points

def calculate_session_points(result, driver, session_type, race=None):
    session_points = Decimal('0.0')
    if not result:
        return session_points

    if session_type == 'Qualifying':
        if result.position <= 10:
            session_points += Decimal('2.0')
        if result.position == 1:
            session_points += Decimal('3.0')

    elif session_type in ['Sprint', 'Race']:
        base_points = get_base_points(result.position, session_type)
        session_points += adjust_points_by_tier(driver, base_points, session_type, result, race)
        if result.fastest_lap and 1 <= result.position <= 10:
            session_points += Decimal('1.0')

    return session_points

def calculate_driver_session_points(selection):
    driver_points_list = []
    for driver in selection.drivers.all():
        points_breakdown = {}
        total_points = Decimal('0.00')
        for session_type in ['Qualifying', 'Sprint', 'Race']:
            result = RaceResult.objects.filter(race=selection.race, driver=driver, session_type=session_type).first()
            session_points = calculate_session_points(result, driver, session_type, selection.race)
            points_breakdown[session_type] = session_points
            total_points += session_points
        driver_points_list.append({
            'driver': driver,
            'points_breakdown': points_breakdown,
            'total_points': total_points
        })
    return driver_points_list

def calculate_team_selection_points(selection):
    selection.points = Decimal('0.0')
    
    # Calculate points for each driver in the selection
    for driver in selection.drivers.all():
        for session_type in ['Qualifying', 'Sprint', 'Race']:
            result = RaceResult.objects.filter(race=selection.race, driver=driver, session_type=session_type).first()
            session_points = calculate_session_points(result, driver, session_type, selection.race)
            selection.points += session_points
    
    # Add prediction points for this race week if applicable
    prediction_answer = PredictionAnswer.objects.filter(
        team=selection.team, 
        prediction_question__race=selection.race
    ).first()
    if prediction_answer and prediction_answer.is_correct:
        selection.points += prediction_answer.points_earned
    
    selection.save()

def calculate_total_team_points(team):
    total_points = Decimal('0.0')
    
    # Calculate total points across all team selections
    team_selections = TeamSelection.objects.filter(team=team)
    for selection in team_selections:
        calculate_driver_session_points(selection)
        total_points += selection.points  # This now includes prediction points

    return total_points

def calculate_team_points(race):
    team_selections = TeamSelection.objects.filter(race=race)
    
    for selection in team_selections:
        selection.points = Decimal('0.0')
        
        # Calculate points for each driver in the selection
        for driver in selection.drivers.all():
            for session_type in ['Qualifying', 'Sprint', 'Race']:
                result = RaceResult.objects.filter(race=race, driver=driver, session_type=session_type).first()
                session_points = calculate_session_points(result, driver, session_type, race)
                selection.points += session_points
        
        # Add prediction points for this race week if applicable
        prediction_answer = PredictionAnswer.objects.filter(
            team=selection.team, 
            prediction_question__race=race
        ).first()
        if prediction_answer and prediction_answer.is_correct:
            selection.points += prediction_answer.points_earned
        
        selection.save()

def calculate_driver_performance(driver, league):
    total_points = Decimal('0.0')
    for result in driver.race_results.filter(race__league=league):
        race = result.race if result.race else None
        session_points = calculate_session_points(result, driver, result.session_type, race)
        total_points += session_points
    return total_points
import requests
from .models import Race, Driver, RaceResult

ERGAST_BASE_URL = "https://api.jolpi.ca/ergast/f1/"

def fetch_driver_race_results(season=2024):
    """
    Fetch results for all races in the specified season.
    """
    # Get all RaceTemplate entries for the specified season
    race_templates = RaceTemplate.objects.filter(season=season)

    # Iterate over each race template
    for race_template in race_templates:
        # Fetch results for all associated Race instances across leagues
        races = Race.objects.filter(template=race_template)
        for race in races:
            # Qualifying Results
            fetch_session_results(race, session_type='Qualifying')

            # Sprint Results (if applicable)
            fetch_session_results(race, session_type='Sprint')

            # Race Results
            fetch_session_results(race, session_type='Race')

    return f"Successfully fetched all session results for the {season} season"

def fetch_session_results(race, session_type):
    """
    Fetch and store results for a specific session type (Qualifying, Sprint, Race)
    for a given race. Utilizes RaceTemplate details for season and round.
    """
    # Retrieve season and round from the RaceTemplate associated with this race
    race_template = race.template
    season = race_template.season
    round_number = race_template.round

    # Determine URL and result key based on session type
    if session_type == 'Qualifying':
        url = f"{ERGAST_BASE_URL}/{season}/{round_number}/qualifying.json"
        results_key = 'QualifyingResults'
    elif session_type == 'Sprint':
        url = f"{ERGAST_BASE_URL}/{season}/{round_number}/sprint.json"
        results_key = 'SprintResults'
    elif session_type == 'Race':
        url = f"{ERGAST_BASE_URL}/{season}/{round_number}/results.json"
        results_key = 'Results'
    else:
        print(f"Unsupported session type: {session_type}")
        return

    # Fetch data from the API
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {session_type} data for race {race_template.name}: {response.status_code}")
        return

    data = response.json()
    race_data = data.get('MRData', {}).get('RaceTable', {}).get('Races', [])

    if not race_data or results_key not in race_data[0]:
        print(f"No {session_type} data available for race {race_template.name}")
        return

    # Iterate over the session results
    for result_data in race_data[0][results_key]:
        driver_data = result_data['Driver']
        constructor_data = result_data['Constructor']

        # Get or create the constructor
        constructor, _ = Constructor.objects.get_or_create(
            name=constructor_data['name']
        )

        # Get or create the driver with the constructor linked
        driver, _ = Driver.objects.get_or_create(
            driver_id=driver_data['driverId'],
            defaults={
                'name': f"{driver_data['givenName']} {driver_data['familyName']}",
                'nationality': driver_data.get('nationality', 'Unknown'),
                'constructor': constructor
            }
        )

        # Extract data based on session type
        if session_type == 'Qualifying':
            position = int(result_data.get('position', 0))
            points = 0  # Qualifying doesn't have points
            fastest_lap = False  # Not applicable for qualifying
        elif session_type == 'Sprint':
            position = int(result_data.get('position', 0))
            points = float(result_data.get('points', 0))
            # Determine if this driver achieved the fastest lap
            fastest_lap = result_data.get('FastestLap', {}).get('rank') == "1"
        elif session_type == 'Race':
            position = int(result_data.get('position', 0))
            points = float(result_data.get('points', 0))
            # Determine if this driver achieved the fastest lap
            fastest_lap = result_data.get('FastestLap', {}).get('rank') == "1"

        # Create or update RaceResult for the driver in the specific session
        RaceResult.objects.update_or_create(
            race=race,
            driver=driver,
            session_type=session_type,
            defaults={
                'position': position,
                'points': points,
                'fastest_lap': fastest_lap,
            }
        )
    print(f"Fetched {session_type} data for race {race_template.name}")

def fetch_historical_standings_for_race(race):
    """
    Fetch and store historical standings for all constructors at the time of a specific race.
    """
    # Define the endpoint for constructor standings based on race season and round
    url = f"{ERGAST_BASE_URL}/{race.template.season}/{race.template.round}/constructorStandings.json"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to fetch standings for {race.template.name} - Status Code: {response.status_code}")
        return

    data = response.json()
    standings = data.get('MRData', {}).get('StandingsTable', {}).get('StandingsLists', [])

    if not standings:
        print(f"No standings data found for {race.template.name}")
        return

    # Standings for this race
    for position, standing_data in enumerate(standings[0].get('ConstructorStandings', []), start=1):
        constructor_id = standing_data['Constructor']['name']
        
        # Get the constructor instance
        constructor = Constructor.objects.filter(name=constructor_id).first()
        if not constructor:
            print(f"Constructor {constructor_id} not found in database.")
            continue

        # Create or update historical standings for this race and constructor
        HistoricalConstructorStanding.objects.update_or_create(
            race=race,
            constructor=constructor,
            defaults={'standing': position}
        )
    print(f"Historical standings saved for {race.template.name}")

def populate_historical_standings_for_all_races():
    """
    Populate historical standings for all past races.
    """
    past_races = Race.objects.filter(template__date__lt=timezone.now().date())

    for race in past_races:
        fetch_historical_standings_for_race(race)
    print("Historical standings populated for all past races.")

def calculate_total_driver_points(past_selections, total_prediction_points=Decimal('0.0')):
    """
    Calculate total points for each driver based on past selections, accumulating points for all drivers.
    Args:
        past_selections: A queryset of TeamSelection instances representing past selections for a team.
        total_prediction_points: Decimal representing points from prediction questions (optional).
    Returns:
        A dictionary with the total points for each driver and the overall team total.
    """
    driver_points = {}

    # Calculate points based on past selections
    for selection in past_selections:
        # Calculate points for each driver in the selection
        driver_sessions_points = calculate_driver_session_points(selection)
        
        for session in driver_sessions_points:
            driver = session['driver']
            driver_points_for_session = session['total_points']

            # Accumulate points for each driver
            if driver not in driver_points:
                driver_points[driver] = driver_points_for_session
            else:
                driver_points[driver] += driver_points_for_session

    # Calculate the final team total including prediction points
    team_total_points = sum(points for points in driver_points.values()) + total_prediction_points

    return {
        'driver_points': driver_points,
        'team_total_points': team_total_points
    }


def determine_current_season_half(current_race_round, total_races=24):
    """Determines the current season half (1 or 2) based on race round and total number of races."""
    halfway_point = total_races // 2
    return 1 if current_race_round <= halfway_point else 2