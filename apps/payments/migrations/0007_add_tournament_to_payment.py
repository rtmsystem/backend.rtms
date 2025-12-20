# Generated migration to add tournament relationship to Payment

import django.core.validators
import django.utils.timezone
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0006_remove_payment_payments_pa_tournam_02464a_idx_and_more'),
        ('tournaments', '0010_tournament_banner'),
    ]

    operations = [
        # Add tournament field as nullable OneToOneField
        migrations.AddField(
            model_name='payment',
            name='tournament',
            field=models.OneToOneField(
                blank=True,
                help_text='Tournament this payment configuration belongs to (inherited by all divisions)',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='payment',
                to='tournaments.tournament',
                verbose_name='Tournament'
            ),
        ),
        # Convert division from OneToOneField to ForeignKey (nullable)
        migrations.AlterField(
            model_name='payment',
            name='division',
            field=models.ForeignKey(
                blank=True,
                help_text='Division this payment configuration belongs to (overrides tournament configuration)',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='payment',
                to='tournaments.tournamentdivision',
                verbose_name='Division'
            ),
        ),
        # Add index for tournament
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['tournament'], name='payments_pa_tournament_idx'),
        ),
        # Add constraint to ensure only one of tournament or division is set
        migrations.AddConstraint(
            model_name='payment',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(tournament__isnull=False, division__isnull=True) |
                    models.Q(tournament__isnull=True, division__isnull=False)
                ),
                name='payment_must_have_tournament_or_division'
            ),
        ),
    ]


