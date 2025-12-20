# Generated manually for adding invoice_number and PaymentTransactionItem

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone
from decimal import Decimal


def generate_invoice_numbers(apps, schema_editor):
    """Generate invoice numbers for existing PaymentTransaction records."""
    PaymentTransaction = apps.get_model('payments', 'PaymentTransaction')
    db_alias = schema_editor.connection.alias
    
    transactions = PaymentTransaction.objects.using(db_alias).filter(
        invoice_number__isnull=True
    ).order_by('id')
    
    invoice_counter = 1
    for transaction in transactions:
        # Check if there's already a transaction with this number
        while PaymentTransaction.objects.using(db_alias).filter(
            invoice_number=f'INV-{invoice_counter}'
        ).exists():
            invoice_counter += 1
        
        transaction.invoice_number = f'INV-{invoice_counter}'
        transaction.save(update_fields=['invoice_number'])
        invoice_counter += 1


def reverse_generate_invoice_numbers(apps, schema_editor):
    """Reverse: clear invoice numbers (optional, for rollback)."""
    PaymentTransaction = apps.get_model('payments', 'PaymentTransaction')
    db_alias = schema_editor.connection.alias
    
    PaymentTransaction.objects.using(db_alias).update(invoice_number=None)


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0011_remove_paymenttransaction_payments_pa_involve_489cb6_idx_and_more'),
        ('tournaments', '0010_tournament_banner'),
    ]

    operations = [
        # Step 1: Add invoice_number field (nullable initially)
        migrations.AddField(
            model_name='paymenttransaction',
            name='invoice_number',
            field=models.CharField(
                blank=True,
                help_text='Auto-generated sequential invoice number (e.g., INV-1, INV-2)',
                max_length=50,
                null=True,
                unique=True,
                verbose_name='Invoice Number'
            ),
        ),
        # Step 2: Generate invoice numbers for existing transactions
        migrations.RunPython(
            generate_invoice_numbers,
            reverse_generate_invoice_numbers,
        ),
        # Step 3: Create PaymentTransactionItem model
        migrations.CreateModel(
            name='PaymentTransactionItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('division_name', models.CharField(help_text='Snapshot of division name at time of transaction', max_length=255, verbose_name='Division Name')),
                ('subscription_fee', models.DecimalField(decimal_places=2, help_text='Base subscription fee for this division', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Subscription Fee')),
                ('early_payment_discount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Early payment discount applied to this item', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Early Payment Discount')),
                ('second_category_discount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Second category discount applied to this item', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Second Category Discount')),
                ('item_total', models.DecimalField(decimal_places=2, help_text='Total amount for this item after discounts (subscription_fee - discounts)', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Item Total')),
                ('created_at', models.DateTimeField(default=timezone.now, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('involvement', models.OneToOneField(help_text='Involvement (division registration) this item represents', on_delete=django.db.models.deletion.CASCADE, related_name='payment_transaction_item', to='tournaments.involvement', verbose_name='Involvement')),
                ('transaction', models.ForeignKey(help_text='Payment transaction this item belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='items', to='payments.paymenttransaction', verbose_name='Transaction')),
            ],
            options={
                'verbose_name': 'Payment Transaction Item',
                'verbose_name_plural': 'Payment Transaction Items',
                'ordering': ['transaction', 'created_at'],
            },
        ),
        # Step 4: Add indexes for PaymentTransactionItem
        migrations.AddIndex(
            model_name='paymenttransactionitem',
            index=models.Index(fields=['transaction'], name='payments_pa_transac_idx'),
        ),
        migrations.AddIndex(
            model_name='paymenttransactionitem',
            index=models.Index(fields=['involvement'], name='payments_pa_involv_idx'),
        ),
        # Step 5: Add index for invoice_number
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['invoice_number'], name='payments_pa_invoice_idx'),
        ),
    ]

