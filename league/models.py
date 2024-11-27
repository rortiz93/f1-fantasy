from django.contrib.auth.models import User  # Django's built-in user model
from django.db import models
from decimal import Decimal
from django.db.models import Sum

class League(models.Model):
    name = models.CharField(max_length=100)
    season = models.IntegerField()
    users = models.ManyToManyField(User, related_name="leagues")  # New field for users in a league

   
    def __str__(self):
        return f"{self.name} - {self.season}"

class Team(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="teams")
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name="leagues")
    name = models.CharField(max_length=100)
    
    class Meta:
        unique_together = ('user', 'league') 
    def __str__(self):
        return f"{self.name} - {self.league.name} ({self.user.username})"

class RaceTemplate(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()
    location = models.CharField(max_length=100)
    season = models.IntegerField(default=2024)  # For example, the 2024 season
    round = models.IntegerField()  # The round of the race in the season
    circuit = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        unique_together = ('season', 'round')  # Ensures unique race templates per season and round

    def __str__(self):
        return f"{self.name} - Round {self.round} ({self.season})"
class Race(models.Model):
    template = models.ForeignKey(RaceTemplate, on_delete=models.CASCADE, blank=True, null=True,related_name="races")
    league = models.ForeignKey(League, on_delete=models.CASCADE,blank=True, null=True, related_name="races")
    lineup_deadline = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.template.name} - {self.template.season} ({self.league.name})"

class Constructor(models.Model):
    name = models.CharField(max_length=100, unique=True)
    standing = models.IntegerField(blank=True, null=True)  # Current standing in the season

    def __str__(self):
        return self.name


    
class Driver(models.Model):

    driver_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    constructor = models.ForeignKey(Constructor, on_delete=models.SET_NULL, null=True, blank=True, related_name="drivers")
    tier = models.IntegerField(null=True, blank=True, default=None)  # Placeholder default
    price = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.name} - Tier {self.tier if self.tier else 'Not Set'}"
    
class TeamSelection(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, blank=True, null=True, related_name="selections")
    race = models.ForeignKey(Race, on_delete=models.CASCADE,  related_name="team_selections")
    drivers = models.ManyToManyField(Driver, related_name="drivers")
    total_cost = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    submitted_on_time = models.BooleanField(default=True)  # True if submitted by Thursday night, false if late but before Friday 12 PM
    points = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    class Meta:
        unique_together = ('team', 'race')  # Ensure one selection per team per race
    def user_username(self):
        return self.team.user.username if self.team and self.team.user else "N/A"
    def __str__(self):
        return f"{self.team.name} - {self.race.template.name} ({self.race.template.date})"

    user_username.short_description = "User Username"
class RaceResult(models.Model):
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, null=True, blank=True, related_name='race_results')
    position = models.IntegerField()
    points = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    fastest_lap = models.BooleanField(default=False)
    dnf = models.BooleanField(default=False)
    session_type = models.CharField(max_length=10, choices=[('Qualifying', 'Qualifying'), ('Race', 'Race'), ('Sprint', 'Sprint')])
    is_tier_override = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.driver.name if self.driver else 'Unknown Driver'} - {self.race.template.name} - {self.session_type}"



class HistoricalConstructorStanding(models.Model):
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="historical_standings")
    constructor = models.ForeignKey(Constructor, on_delete=models.CASCADE)
    standing = models.IntegerField()

    class Meta:
        unique_together = ('race', 'constructor')  # Each constructor has a unique standing per race

    def __str__(self):
        return f"{self.constructor.name} - Standing {self.standing} for {self.race.template.name}"
    
class PredictionQuestion(models.Model):
    race = models.OneToOneField(Race, on_delete=models.CASCADE, related_name='prediction_question')
    question_text = models.TextField()
    question_type = models.CharField(max_length=50, choices=[('text', 'Text'), ('multiple_choice', 'Multiple Choice')])
    options = models.JSONField(blank=True, null=True)  # Only for multiple-choice questions
    points_awarded = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.0'))
    correct_answer = models.CharField(max_length=255, blank=True, null=True)  # Expected answer to compare

    def __str__(self):
        return f"Prediction for {self.race.template.name} - {self.race.template.date}"

class PredictionAnswer(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='prediction_answers')
    prediction_question = models.ForeignKey(PredictionQuestion, on_delete=models.CASCADE, related_name='answers')
    answer = models.CharField(max_length=255)
    points_earned = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.0'))
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.team.name} - {self.prediction_question.race.template.name}"