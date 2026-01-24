"""
URL configuration for tournaments app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = "tournaments"

# Tournament URLs with organization_id
tournament_urlpatterns = [
    # Tournament CRUD
    path("", views.TournamentListCreateView.as_view(), name="tournament-list-create"),
    path(
        "<int:pk>/",
        views.TournamentRetrieveUpdateDestroyView.as_view(),
        name="tournament-detail",
    ),
    # Tournament actions
    path("<int:pk>/publish/", views.tournament_publish, name="tournament-publish"),
    path("<int:pk>/cancel/", views.tournament_cancel, name="tournament-cancel"),
    # Tournament divisions
    path(
        "<int:tournament_id>/divisions/",
        views.TournamentDivisionListCreateView.as_view(),
        name="tournament-division-list-create",
    ),
    path(
        "<int:tournament_id>/divisions/<int:pk>/",
        views.TournamentDivisionRetrieveUpdateDestroyView.as_view(),
        name="tournament-division-detail",
    ),
    # Tournament involvements
    path(
        "<int:tournament_id>/involvements/",
        views.InvolvementListCreateView.as_view(),
        name="tournament-involvement-list-create",
    ),
    path(
        "<int:tournament_id>/involvements/<int:pk>/",
        views.InvolvementRetrieveUpdateDestroyView.as_view(),
        name="tournament-involvement-detail",
    ),
    path(
        "<int:tournament_id>/involvements/<int:pk>/approve/",
        views.approve_involvement,
        name="tournament-involvement-approve",
    ),
    path(
        "<int:tournament_id>/involvements/<int:pk>/reject/",
        views.reject_involvement,
        name="tournament-involvement-reject",
    ),
    path(
        "<int:tournament_id>/involvements/<int:pk>/toggle-payment/",
        views.toggle_payment_status,
        name="tournament-involvement-toggle-payment",
    ),
    # Utility endpoints
    path("choices/", views.tournament_choices, name="tournament-choices"),
    path("<int:tournament_id>/divisions/<int:pk>/publish/",
        views.publish_division,
        name="publish-division",
    ),
    path("<int:tournament_id>/divisions/<int:pk>/generate-groups/",
        views.generate_groups,
        name="generate-groups",
    ),
    path("<int:tournament_id>/divisions/<int:pk>/calculate-standings/",
        views.calculate_standings,
        name="calculate-standings",
    ),
]

urlpatterns = tournament_urlpatterns
