from django.contrib import admin

# Register your models here.

from .models import Race, TeamSelection, RaceResult, League, Constructor, Driver, Team, RaceTemplate, PredictionAnswer, PredictionQuestion
from .utils import calculate_team_points


class RaceResultAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        calculate_team_points(obj.race)  # Calculate points after saving result



class RaceTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'season', 'round', 'date', 'location', 'circuit')
    list_filter = ('season',)
    search_fields = ('name', 'location', 'circuit')
    ordering = ('season', 'round')
class RaceAdmin(admin.ModelAdmin):
    list_display = ('template', 'league', 'lineup_deadline')
    list_filter = ('league', 'template__season')
    search_fields = ('template__name', 'league__name')
    ordering = ('template__season', 'template__round')
class RaceInline(admin.TabularInline):
    model = Race
    extra = 1  # Number of blank fields to display for new entries

class LeagueAdmin(admin.ModelAdmin):
    inlines = [RaceInline]
    list_display = ('name', 'season')
    search_fields = ('name',)

admin.site.register(League, LeagueAdmin)

admin.site.register(PredictionQuestion)

admin.site.register(PredictionAnswer)

admin.site.register(RaceTemplate, RaceTemplateAdmin)

admin.site.register(TeamSelection)

admin.site.register(RaceResult, RaceResultAdmin)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'league')

@admin.register(Constructor)
class ConstructorAdmin(admin.ModelAdmin):
    list_display = ('name', 'standing')  # Customize fields to display in admin list view

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'constructor')  # Customize fields to display in admin list view
