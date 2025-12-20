"""
API URL configuration.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.geographical.urls import urlpatterns as geographical_urls
from apps.organizations.views import OrganizationViewSet
from apps.players.views import PlayerProfileViewSet
from apps.tournaments.urls import urlpatterns as tournament_urls
from apps.matches.urls import urlpatterns as match_urls
from apps.payments.urls import (
    tournament_payment_urlpatterns as tournament_payment_urls,
    division_payment_urlpatterns as division_payment_urls,
    payment_transaction_urlpatterns as payment_transaction_urls
)
from apps.payments import views as payment_views
from .views import UserViewSet, auth_views

app_name = 'api'

# Router for viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'player-profiles', PlayerProfileViewSet, basename='playerprofile')

urlpatterns = [
    # API versioning
    path('v1/', include([
        # Authentication endpoints
        path('auth/login/', auth_views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('auth/refresh/', auth_views.CustomTokenRefreshView.as_view(), name='token_refresh'),
        path('auth/logout/', auth_views.LogoutView.as_view(), name='logout'),
        path('auth/me/', auth_views.CurrentUserView.as_view(), name='current-user'),
        path('auth/verify/', auth_views.VerifyTokenView.as_view(), name='verify-token'),
        
        # Router URLs
        path('', include(router.urls)),
        
        # Tournament URLs (without organization_id - uses authenticated user's organization)
        path('tournaments/', include(tournament_urls)),
        
        # Geographical URLs (públicas)
        path('geographical/', include(geographical_urls)),
        
        # Match URLs
        path('matches/', include(match_urls)),
        
        # Payment URLs (tournament level)
        path('tournaments/<int:tournament_id>/payment/', include(tournament_payment_urls)),
        
        # Payment URLs (division level)
        path('tournaments/<int:tournament_id>/divisions/<int:division_id>/payment/', include(division_payment_urls)),
        
        # Bulk create payments for all tournament divisions
        path(
            'tournaments/<int:tournament_id>/payments/bulk-create/',
            payment_views.bulk_create_tournament_payments,
            name='bulk-create-tournament-payments'
        ),
        
        # Tournament payment transactions
        path(
            'tournaments/<int:tournament_id>/transactions/',
            payment_views.get_tournament_transactions,
            name='tournament-transactions'
        ),
        
        # Player transactions in tournament
        path(
            'tournaments/<int:tournament_id>/players/<int:player_id>/transactions/',
            payment_views.get_player_tournament_transactions,
            name='player-tournament-transactions'
        ),
        
        # Payment transaction URLs
        path('payments/', include(payment_transaction_urls)),
        
        # Payment transaction detail
        path(
            'payments/transactions/<int:transaction_id>/',
            payment_views.get_transaction_detail,
            name='transaction-detail'
        ),
    ])),
]