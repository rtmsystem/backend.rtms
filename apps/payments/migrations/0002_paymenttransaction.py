# Generated migration for PaymentTransaction model

import django.core.validators
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
        ('tournaments', '0010_tournament_banner'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentTransaction',
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
                    'amount',
                    models.DecimalField(
                        decimal_places=2,
                        help_text='Payment amount',
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0.01)],
                        verbose_name='Amount'
                    )
                ),
                (
                    'subscription_fee',
                    models.DecimalField(
                        decimal_places=2,
                        help_text='Original subscription fee',
                        max_digits=10,
                        verbose_name='Subscription Fee'
                    )
                ),
                (
                    'early_payment_discount',
                    models.DecimalField(
                        decimal_places=2,
                        default=0.0,
                        help_text='Early payment discount applied',
                        max_digits=10,
                        verbose_name='Early Payment Discount'
                    )
                ),
                (
                    'second_category_discount',
                    models.DecimalField(
                        decimal_places=2,
                        default=0.0,
                        help_text='Second category discount applied',
                        max_digits=10,
                        verbose_name='Second Category Discount'
                    )
                ),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('pending', 'Pending'),
                            ('processing', 'Processing'),
                            ('completed', 'Completed'),
                            ('failed', 'Failed'),
                            ('cancelled', 'Cancelled'),
                            ('refunded', 'Refunded')
                        ],
                        default='pending',
                        help_text='Payment transaction status',
                        max_length=20,
                        verbose_name='Status'
                    )
                ),
                (
                    'payment_method',
                    models.CharField(
                        choices=[
                            ('cash', 'Cash'),
                            ('bank_transfer', 'Bank Transfer'),
                            ('credit_card', 'Credit Card'),
                            ('debit_card', 'Debit Card'),
                            ('stripe', 'Stripe'),
                            ('paypal', 'PayPal'),
                            ('other', 'Other')
                        ],
                        help_text='Method used for payment',
                        max_length=20,
                        verbose_name='Payment Method'
                    )
                ),
                (
                    'transaction_id',
                    models.CharField(
                        blank=True,
                        help_text='External transaction ID (from payment gateway)',
                        max_length=255,
                        null=True,
                        unique=True,
                        verbose_name='Transaction ID'
                    )
                ),
                (
                    'payment_reference',
                    models.CharField(
                        blank=True,
                        help_text='Payment reference number',
                        max_length=255,
                        null=True,
                        verbose_name='Payment Reference'
                    )
                ),
                (
                    'notes',
                    models.TextField(
                        blank=True,
                        help_text='Additional notes about the payment',
                        null=True,
                        verbose_name='Notes'
                    )
                ),
                (
                    'payment_proof',
                    models.FileField(
                        blank=True,
                        help_text='Payment proof document (PDF or image)',
                        null=True,
                        upload_to='payment_proofs/',
                        validators=[
                            django.core.validators.FileExtensionValidator(
                                allowed_extensions=['pdf', 'png', 'jpg', 'jpeg']
                            )
                        ],
                        verbose_name='Payment Proof'
                    )
                ),
                (
                    'processed_at',
                    models.DateTimeField(
                        blank=True,
                        help_text='When the payment was processed',
                        null=True,
                        verbose_name='Processed At'
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
                    'involvement',
                    models.ForeignKey(
                        help_text='Involvement this payment is for',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='payment_transactions',
                        to='tournaments.involvement',
                        verbose_name='Involvement'
                    )
                ),
                (
                    'processed_by',
                    models.ForeignKey(
                        blank=True,
                        help_text='User who processed this payment',
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='processed_payments',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='Processed By'
                    )
                ),
            ],
            options={
                'verbose_name': 'Payment Transaction',
                'verbose_name_plural': 'Payment Transactions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['involvement'], name='payments_pa_involve_idx'),
        ),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['status'], name='payments_pa_status_idx'),
        ),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['transaction_id'], name='payments_pa_transac_idx'),
        ),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['payment_method'], name='payments_pa_payment_idx'),
        ),
    ]

