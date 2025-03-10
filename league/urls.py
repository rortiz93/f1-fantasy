from django.urls import path
from . import views

from django.contrib.auth import views as auth_views
from django.urls import path
from .views import CustomLoginView



urlpatterns = [
    path('register/', views.register, name='register'),
    path('', views.home_view, name='home_view'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'), 
    path('league/<int:league_id>/', views.league_view, name='league'),
    path('profile/', views.profile, name='profile'),
    path('league/<int:league_id>/team/<int:team_id>/race/<int:pk>/select-team', views.RaceDetailView.as_view(), name='race_selection'),
    path('league/<int:league_id>/team/<int:team_id>/', views.team_view, name='team_view'),
    path('league/<int:league_id>/race-calendar/', views.race_calendar_view, name='race_calendar'),
    path('league/<int:league_id>/race/<int:race_id>/', views.race_detail_view, name='race_detail'),
    path('join-league/<int:league_id>/', views.join_league, name='join_league'),
    path('create-team/<int:league_id>/', views.create_team, name='create_team'),
    path('league/<int:league_id>/team/<int:team_id>/activate-mulligan/', views.activate_mulligan, name='activate_mulligan'),
    path('league/<int:league_id>/team/<int:team_id>/activate-overdrive/', views.activate_overdrive, name='activate_overdrive'),
    path('league/<int:league_id>/team/<int:team_id>/set-overdrive-driver/', views.set_overdrive_driver, name='set_overdrive_driver'),
]