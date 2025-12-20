"""
Constants and choices for matches app.
"""
from django.db import models


class MatchType(models.TextChoices):
    """Match type choices."""
    SINGLES = 'singles', 'Singles'
    DOUBLES = 'doubles', 'Doubles'


class MatchStatus(models.TextChoices):
    """Match status choices."""
    PENDING = 'pending', 'Pending'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class SetWinner(models.TextChoices):
    """Set winner choices."""
    PLAYER1 = 'player1', 'Player 1'
    PLAYER2 = 'player2', 'Player 2'

