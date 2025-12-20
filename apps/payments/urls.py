"""
URL configuration for payments app.
"""
from django.urls import path

from . import views

app_name = "payments"

# Payment URLs with tournament_id and division_id
payment_urlpatterns = [
    # Payment details calculation (kept for backward compatibility)
    path(
        "divisions/<int:division_id>/payment-details/",
        views.get_payment_details,
        name="payment-details",
    ),
]

# Payment URLs for tournament-specific configuration
tournament_payment_urlpatterns = [
    # Payment CRUD for tournament
    path(
        "",
        views.PaymentViewSet.as_view({
            'get': 'retrieve',
            'post': 'create',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name="tournament-payment-detail",
    ),
]

# Payment URLs for division-specific configuration
division_payment_urlpatterns = [
    # Payment CRUD for division
    path(
        "",
        views.PaymentViewSet.as_view({
            'get': 'retrieve',
            'post': 'create',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name="division-payment-detail",
    ),
]

urlpatterns = payment_urlpatterns

# Export transaction URLs separately for API integration
payment_transaction_urlpatterns = [
    # Payment transactions
    path(
        "transactions/",
        views.create_payment_transaction,
        name="create-payment-transaction",
    ),
    path(
        "transactions/<int:transaction_id>/confirm/",
        views.confirm_payment,
        name="confirm-payment",
    ),
    path(
        "involvements/<int:involvement_id>/transactions/",
        views.get_involvement_payments,
        name="involvement-payments",
    ),
]

urlpatterns = payment_urlpatterns
