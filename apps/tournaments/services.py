from django.db import transaction
from typing import Optional
from django.contrib.auth import get_user_model
import logging

from .models import TournamentDivision

logger = logging.getLogger(__name__)
User = get_user_model()


class DivisionCompletionService:

    def __init__(self, division: TournamentDivision, user: Optional[User] = None) -> None:
        self.division = division
        self.user = user

    @transaction.atomic
    def publish_division(self) -> TournamentDivision:
        self.division.publish(user=self.user)
        
        logger.info(
            f"Division {self.division.id} ({self.division.name}) "
            f"published by user {self.user.id if self.user else 'system'}"
        )
        
        return self.division