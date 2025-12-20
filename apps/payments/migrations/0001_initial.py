# Generated migration for payments app

import django.core.validators
import django.utils.timezone
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tournaments', '0010_tournament_banner'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'subscription_fee',
                    models.DecimalField(
                        decimal_places=2,
                        help_text='Base subscription fee for this division',
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0.0)],
                        verbose_name='Subscription Fee'
                    )
                ),
                (
                    'early_payment_discount_amount',
                    models.DecimalField(
                        decimal_places=2,
                        default=0.0,
                        help_text='Discount amount for early payment',
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0.0)],
                        verbose_name='Early Payment Discount Amount'
                    )
                ),
                (
                    'early_payment_discount_deadline',
                    models.DateTimeField(
                        blank=True,
                        help_text='Deadline date for applying early payment discount',
                        null=True,
                        verbose_name='Early Payment Discount Deadline'
                    )
                ),
                (
                    'second_category_discount_amount',
                    models.DecimalField(
                        decimal_places=2,
                        default=0.0,
                        help_text='Discount amount for registering in a second category',
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0.0)],
                        verbose_name='Second Category Discount Amount'
                    )
                ),
                (
                    'is_active',
                    models.BooleanField(
                        default=True,
                        help_text='Whether payment subscription is active for this division',
                        verbose_name='Active'
                    )
                ),
                (
                    'created_at',
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        verbose_name='Created At'
                    )
                ),
                (
                    'updated_at',
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name='Updated At'
                    )
                ),
                (
                    'tournament',
                    models.OneToOneField(
                        help_text='Tournament this payment configuration belongs to',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='payment',
                        to='tournaments.tournament',
                        verbose_name='Tournament'
                    )
                ),
            ],
            options={
                'verbose_name': 'Payment',
                'verbose_name_plural': 'Payments',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['tournament'], name='payments_pa_tournam_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['is_active'], name='payments_pa_is_acti_idx'),
        ),
    ]

