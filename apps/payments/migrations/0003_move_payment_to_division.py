# Generated migration to move Payment from Tournament to TournamentDivision

import django.core.validators
import django.utils.timezone
from django.db import migrations, models
import django.db.models.deletion


def migrate_payments_to_divisions(apps, schema_editor):
    """
    Migrate existing payments from tournaments to divisions.
    This creates a payment for each division in tournaments that have payments.
    """
    Payment = apps.get_model('payments', 'Payment')
    TournamentDivision = apps.get_model('tournaments', 'TournamentDivision')
    
    # Get all payments with tournament relationship
    # Note: This will be empty in fresh installs, but handles existing data
    for payment in Payment.objects.all():
        if hasattr(payment, 'tournament') and payment.tournament:
            # Create payment config for each division in the tournament
            divisions = TournamentDivision.objects.filter(tournament=payment.tournament)
            for division in divisions:
                # Only create if division doesn't already have a payment
                if not Payment.objects.filter(division=division).exists():
                    Payment.objects.create(
                        division=division,
                        subscription_fee=payment.subscription_fee,
                        early_payment_discount_amount=payment.early_payment_discount_amount,
                        early_payment_discount_deadline=payment.early_payment_discount_deadline,
                        second_category_discount_amount=payment.second_category_discount_amount,
                        is_active=payment.is_active,
                        created_at=payment.created_at,
                        updated_at=payment.updated_at
                    )


def remove_old_index_if_exists(apps, schema_editor):
    """
    Remove old tournament index if it exists.
    The index might have been renamed, so we try both possible names.
    """
    connection = schema_editor.connection
    
    # Try to find and drop the index if it exists
    # Check for both possible index names
    for index_name in ['payments_pa_tournam_02464a_idx', 'payments_pa_tournam_idx']:
        with connection.cursor() as cursor:
            # Check if index exists (PostgreSQL specific)
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'payments_payment' 
                AND indexname = %s
            """, [index_name])
            if cursor.fetchone():
                # Index exists, drop it using raw SQL
                quoted_name = schema_editor.quote_name(index_name)
                cursor.execute(f'DROP INDEX IF EXISTS {quoted_name}')
                break


def reverse_remove_index(apps, schema_editor):
    """Reverse operation - do nothing as we can't recreate the old index."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_paymenttransaction'),
        ('payments', '0002_rename_payments_pa_tournam_idx_payments_pa_tournam_02464a_idx_and_more'),
        ('tournaments', '0010_tournament_banner'),
    ]

    operations = [
        # Add new division relationship (nullable first)
        migrations.AddField(
            model_name='payment',
            name='division',
            field=models.OneToOneField(
                blank=True,
                help_text='Division this payment configuration belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='payment',
                to='tournaments.tournamentdivision',
                verbose_name='Division'
            ),
        ),
        # Migrate data
        migrations.RunPython(migrate_payments_to_divisions, migrations.RunPython.noop),
        # Remove old index conditionally (it might have been renamed in a previous migration)
        # Must be done before removing the field
        migrations.RunPython(remove_old_index_if_exists, reverse_remove_index, atomic=False),
        # Remove old tournament relationship
        migrations.RemoveField(
            model_name='payment',
            name='tournament',
        ),
        # Add new index
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['division'], name='payments_pa_division_idx'),
        ),
        # Make division field required
        migrations.AlterField(
            model_name='payment',
            name='division',
            field=models.OneToOneField(
                help_text='Division this payment configuration belongs to',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='payment',
                to='tournaments.tournamentdivision',
                verbose_name='Division'
            ),
        ),
    ]

