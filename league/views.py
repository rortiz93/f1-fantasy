from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django import forms
from .forms import TeamSelectionForm, PredictionAnswerForm
from django.utils import timezone
from .models import Race, TeamSelection,RaceResult, Driver, League, Team, RaceTemplate, PredictionQuestion, PredictionAnswer
from django.db.models import Sum, Count
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView
from .utils import calculate_driver_performance, calculate_driver_session_points, calculate_total_driver_points, calculate_team_points, calculate_session_points
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin


from decimal import Decimal
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home_view')
    else:
        form = UserCreationForm()
    return render(request, 'league/register.html', {'form': form})

@login_required
def home_view(request):
    leagues = League.objects.filter(users=request.user)
    
    # Get teams for the user and map them by league ID for easy lookup
    user_teams = {team.league_id: team for team in Team.objects.filter(user=request.user)}

    # Match each league with the corresponding team for the user
    leagues_with_teams = [
        {
            'league_name': league.name,
            'team_name': user_teams[league.id].name if league.id in user_teams else "No Team",
            'league_id': league.id
        }
        for league in leagues
    ]

     # Find the next race based on RaceTemplate's date across all user's leagues
    next_race = (
        Race.objects
        .filter(league__in=leagues, template__date__gte=timezone.now().date())
        .select_related('template')
        .order_by('template__date')
        .first()
    )

    return render(request, 'league/home.html', {
        'leagues_with_teams': leagues_with_teams,
        'next_race': next_race,
    })

class CustomLoginView(LoginView):
    template_name = 'league/login.html'  # Use your login template here

    def form_invalid(self, form):
        # Add a custom error message
        messages.error(self.request, "Incorrect username/password. Please try again.")
        return super().form_invalid(form)

@login_required
def team_view(request, league_id, team_id):
    # Retrieve the team within the specified league and owned by the user
    team = get_object_or_404(Team, id=team_id, league__id=league_id, user=request.user)
    league = team.league
    leagues = League.objects.filter(users=request.user)
    next_race = (
        Race.objects
        .filter(league__in=leagues, template__date__gte=timezone.now().date())
        .select_related('template')
        .order_by('template__date')
        .first()
    )

    # Fetch past race selections for this team based on `RaceTemplate.date`
    past_selections = TeamSelection.objects.filter(
        team=team, 
        race__template__date__lt=timezone.now().date()
    ).order_by('-race__template__date')


    # Initialize dictionaries to store driver points for Tier 1 and Tier 2 drivers
    tier_1_driver_points = {}
    tier_2_driver_points = {}

    # Calculate points based on past selections and league rules
       # Calculate points based on past selections and league rules
    for selection in past_selections:
        # Call the function to calculate points for each driver session
        driver_sessions_points = calculate_driver_session_points(selection)
        
        for session in driver_sessions_points:
            driver = session['driver']
            driver_points = session['total_points']  # Total points for the current driver in this selection

            # Accumulate points based on driver tier
            if driver.tier == 1:
                if driver not in tier_1_driver_points:
                    tier_1_driver_points[driver] = driver_points
                else:
                    tier_1_driver_points[driver] += driver_points
            elif driver.tier == 2:
                if driver not in tier_2_driver_points:
                    tier_2_driver_points[driver] = driver_points
                else:
                    tier_2_driver_points[driver] += driver_points

    # Sort drivers by accumulated points within each tier
    sorted_tier_1_drivers = sorted(
        [{'driver': driver, 'points': points} for driver, points in tier_1_driver_points.items()],
        key=lambda x: x['points'],
        reverse=True
    )
    sorted_tier_2_drivers = sorted(
        [{'driver': driver, 'points': points} for driver, points in tier_2_driver_points.items()],
        key=lambda x: x['points'],
        reverse=True
    )
     # Fetch correct prediction answers and calculate total prediction points
    correct_predictions = PredictionAnswer.objects.filter(
        team=team,
        is_correct=True
    ).annotate(total_points=Sum('points_earned'))

    total_prediction_points = correct_predictions.aggregate(
        total=Sum('points_earned')
    )['total'] or Decimal('0.0')

    
    # Count of Tier 1 driver selections for this team
    tier_1_drivers = Driver.objects.filter(tier=1)
    tier_1_selection_counts = {
        driver: TeamSelection.objects.filter(team=team, drivers=driver).count()
        for driver in tier_1_drivers
    }
    # Calculate the final team total including prediction points for display purposes
    team_total_points = (
        sum(driver['points'] for driver in sorted_tier_1_drivers) +
        sum(driver['points'] for driver in sorted_tier_2_drivers) +
        total_prediction_points
    )
    return render(request, 'league/team.html', {
        'team': team,
        'league': league,
        'next_race': next_race,
        'past_selections': past_selections,
        'top_drivers': sorted_tier_1_drivers,
        'worst_drivers': sorted_tier_2_drivers,
        'tier_1_selection_counts': tier_1_selection_counts,
        'correct_predictions': correct_predictions,
        'total_prediction_points': total_prediction_points,
        'team_total_points': team_total_points,  # For total display
    })
# views.py

@login_required
def race_calendar_view(request, league_id):
    league = get_object_or_404(League, id=league_id)

    # Get the unique RaceTemplate instances for the league’s season
    race_templates = RaceTemplate.objects.filter(season=league.season).order_by('date')
    # Retrieve the team for the user in this league, if it exists
    team = Team.objects.filter(user=request.user, league=league).first()
    # Create a list of races specific to this league, with each race tied to a template
    races = [
        {
            'template': template,
            'race': Race.objects.filter(league=league, template=template).first()
        }
        for template in race_templates
    ]

    return render(request, 'league/race_calendar.html', {
        'league': league,
        'races': races,
        'team': team,
    })

@login_required
def race_detail_view(request, league_id, race_id):
    # Retrieve the specific race within the league
    race = get_object_or_404(Race, id=race_id, league_id=league_id)
    race_template = race.template  # Access RaceTemplate details

    # Check if the race has results (i.e., it has already happened)
    if race_template.date < timezone.now().date():
        # Retrieve top performers for the race, assuming RaceResult has a `position` field
        top_performers = RaceResult.objects.filter(race=race, session_type__in=['Sprint', 'Race']).order_by('position')[:20]
    else:
        top_performers = None

    return render(request, 'league/race_info.html', {
        'race': race,
        'race_template': race_template,
        'top_performers': top_performers,
    })

@login_required
def team_selection(request, race_id):
    race = Race.objects.get(id=race_id)
    if request.method == 'POST':
        form = TeamSelectionForm(request.POST)
        if form.is_valid():
            team_selection = form.save(commit=False)
            team_selection.user = request.user
            team_selection.race = race
            team_selection.total_cost = form.cleaned_data['total_cost']
            team_selection.save()
            form.save_m2m()  # Save the many-to-many relationships (drivers)
            return redirect('profile')  # Redirect to the profile or another page
    else:
        form = TeamSelectionForm()
    return render(request, 'league/team_selection.html', {'form': form, 'race': race})


from .utils import calculate_total_team_points, calculate_team_selection_points
@login_required
def profile(request):
    # Get all teams for the logged-in user
    teams = Team.objects.filter(user=request.user).select_related('league')

    # Organize teams by their league
    user_leagues = []
    for team in teams:
        user_leagues.append({
            'league': team.league,
            'team': team
        })

    return render(request, 'league/profile.html', {'user_leagues': user_leagues})

@login_required
def custom_logout(request):
    logout(request)
    return redirect('login')  # Redirect to home page or any other page
    

@login_required
def league_view(request, league_id):
    league = get_object_or_404(League, id=league_id)
    
    # Get the current user's team in this league
    user_team = Team.objects.filter(league=league, user=request.user).first()

    # Calculate points for each team selection
    for team_selection in TeamSelection.objects.filter(team__league=league):
        calculate_team_selection_points(team_selection)

    # Calculate leaderboard using the new total driver points calculation function
    leaderboard_data = []
    for team in Team.objects.filter(league=league):
        # Fetch past selections for the team
        past_selections = TeamSelection.objects.filter(team=team, race__template__date__lt=timezone.now().date())

        # Calculate prediction points for this team
        total_prediction_points = PredictionAnswer.objects.filter(
            team=team, is_correct=True
        ).aggregate(total=Sum('points_earned'))['total'] or Decimal('0.0')

        # Calculate total driver points including prediction points
        total_points_data = calculate_total_driver_points(past_selections, total_prediction_points)
        total_points = total_points_data['team_total_points']

        leaderboard_data.append({
            'team_name': team.name,
            'points': total_points,
            'is_user_team': team == user_team,
        })

    # Sort leaderboard by total points in descending order
    leaderboard_data.sort(key=lambda x: x['points'], reverse=True)

    # Get all drivers in the league and calculate performance across the season
    all_drivers = Driver.objects.filter(drivers__team__league=league).distinct()
    top_drivers = sorted(
        all_drivers,
        key=lambda driver: calculate_driver_performance(driver, league),
        reverse=True
    )[:5]  # Top 5 drivers based on performance

    # Prepare driver data for the leaderboard
    top_drivers_data = [
        {
            'name': driver.name,
            'constructor': driver.constructor.name,
            'points': calculate_driver_performance(driver, league)
        }
        for driver in top_drivers
    ]

    # Get drivers with price and tier for the table
    drivers = Driver.objects.all().order_by('-price')

    # Calculate points for the latest race
    latest_race = Race.objects.filter(league=league, template__date__lt=timezone.now().date()).order_by('-template__date').first()
    latest_race_points = []
    if latest_race:
        calculate_team_points(latest_race)
        team_selections = TeamSelection.objects.filter(race=latest_race)
        for selection in team_selections:
            driver_points = []
            for driver in selection.drivers.all():
                points_breakdown = {}
                total_driver_points = Decimal('0.0')
                for session_type in ['Qualifying', 'Sprint', 'Race']:
                    result = RaceResult.objects.filter(race=latest_race, driver=driver, session_type=session_type).first()
                    session_points = calculate_session_points(result, driver, session_type, latest_race)
                    points_breakdown[session_type] = session_points
                    total_driver_points += session_points
                driver_points.append({
                    'name': driver.name,
                    'constructor': driver.constructor.name,
                    'points': total_driver_points,
                    'breakdown': points_breakdown,
                })
            latest_race_points.append({
                'team_name': selection.team.name,
                'points': selection.points,
                'drivers': driver_points,
            })
     # Sort latest race by total points in descending order
    latest_race_points.sort(key=lambda x: x['points'], reverse=True)
    return render(request, 'league/league.html', {
        'league': league,
        'user_team': user_team,
        'leaderboard': leaderboard_data,
        'top_drivers': top_drivers_data,
        'drivers': drivers,
        'latest_race_points': latest_race_points,
        'latest_race_name': latest_race.template.name if latest_race else None,
    })
    



from django.utils.timezone import now
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Count, DecimalField, ExpressionWrapper, F
from decimal import Decimal

class RaceDetailView(LoginRequiredMixin, DetailView):
    model = Race
    template_name = 'league/race_detail.html'
    context_object_name = 'race'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        league_id = self.kwargs.get('league_id')
        team_id = self.kwargs.get('team_id')
        context['league_id'] = league_id
        context['team_id'] = team_id
        race = self.object
        # Initialize prediction_form to avoid referencing before assignment
        prediction_form = None
         # Fetch prediction question and answer
        prediction_question = PredictionQuestion.objects.filter(race=race).first()
        prediction_answer = None
        if prediction_question:
            prediction_answer = PredictionAnswer.objects.filter(
                team_id=team_id, prediction_question=prediction_question
            ).first()

        # Fetch the team selection for this race, if it exists
        team_selection = TeamSelection.objects.filter(
            team_id=team_id,
            race=self.object
        ).first()
        context['team_selection'] = team_selection
        context['form'] = TeamSelectionForm(instance=team_selection)

        # Calculate selection count for Tier 1 drivers
        tier_1_driver_usage = (
            TeamSelection.objects.filter(team_id=team_id, race__lineup_deadline__lt=timezone.now())
            .values('drivers__id')
            .annotate(count=Count('drivers__id'))
            .filter(drivers__tier=1)
        )
        context['tier_1_usage'] = {usage['drivers__id']: usage['count'] for usage in tier_1_driver_usage}
        # Initialize TeamSelectionForm
        form = TeamSelectionForm(
            instance=team_selection,
            prediction_question=prediction_question,
            prediction_answer_instance=prediction_answer,
            initial={
                'tier_1_driver': team_selection.drivers.filter(tier=1).first() if team_selection else None,
                'tier_2_drivers': team_selection.drivers.filter(tier=2) if team_selection else [],
                'prediction_answer': prediction_answer.answer if prediction_answer else None,
            },
        )

        context.update({
            'form': form,
            'prediction_question': prediction_question,
            'prediction_answer': prediction_answer,
            'team_selection': team_selection,
            
        })
        # Determine if the race is in the past
        race_date = self.object.template.date
        context['is_past_race'] = race_date < timezone.now().date()

        # If the race is in the past, calculate driver points
        if context['is_past_race'] and team_selection:
            driver_points = calculate_driver_session_points(team_selection)
            context['driver_points'] = driver_points
            context['has_sprint'] = any(
                'Sprint' in dp['points_breakdown'] and dp['points_breakdown']['Sprint'] > 0
                for dp in context['driver_points']
            )
            # Calculate total points for each session type
            context['total_qualifying_points'] = sum(dp['points_breakdown'].get('Qualifying', Decimal(0)) for dp in driver_points)
            context['total_sprint_points'] = sum(dp['points_breakdown'].get('Sprint', Decimal(0)) for dp in driver_points)
            context['total_race_points'] = sum(dp['points_breakdown'].get('Race', Decimal(0)) for dp in driver_points)
            context['total_points'] = sum(Decimal(dp['total_points']) for dp in driver_points)
        else: 
            context['total_points'] = Decimal(0)
        total_points_with_prediction = context['total_points']
        if prediction_form and prediction_form.instance.is_correct:
            total_points_with_prediction += Decimal(prediction_form.instance.points_earned)

        context['total_points_with_prediction'] = total_points_with_prediction

        return context

    def post(self, request, *args, **kwargs):
        # Explicitly set self.object to avoid missing object errors
        self.object = self.get_object()
        
        race = self.object
        league_id = self.kwargs.get('league_id')
        team_id = self.kwargs.get('team_id')

        # Retrieve the team for the current user in the specified league
        team = get_object_or_404(Team, user=request.user, league_id=league_id)

        # Handle prediction answer submission if form is submitted
        prediction_question = PredictionQuestion.objects.filter(race=race).first()
        if prediction_question:
            prediction_answer = PredictionAnswer.objects.filter(
                team=team, prediction_question=prediction_question
            ).first()
            prediction_form = PredictionAnswerForm(request.POST, instance=prediction_answer, prediction_question=prediction_question)
            if prediction_form.is_valid():
                answer_instance = prediction_form.save(commit=False)
                answer_instance.team = team
                answer_instance.prediction_question = prediction_question
                # Award points if the answer is correct
                if answer_instance.answer == prediction_question.correct_answer:
                    answer_instance.points_earned = prediction_question.points_awarded
                    answer_instance.is_correct = True
                answer_instance.save()

        # Handle team selection form submission
        team_selection, created = TeamSelection.objects.get_or_create(team=team, race=race)
        # Process form
        form = TeamSelectionForm(
            request.POST,
            instance=team_selection,
            prediction_question=prediction_question,
            prediction_answer_instance=prediction_answer,
            
        )
        if form.is_valid():
            form.save()  # Save the form to update or create the lineup
            return redirect('race_selection', league_id=league_id, team_id=team_id, pk=race.pk)  # Redirect to the same page after saving

        # If the form is invalid, re-render the page with errors
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)