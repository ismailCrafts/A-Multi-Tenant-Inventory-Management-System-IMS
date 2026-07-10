# Generated migration for StockReservation model

import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authenticate_app', '0001_initial'),
        ('product_app', '0001_initial'),
        ('stock_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockReservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(
                    max_length=100,
                    help_text="User's session key — identifies who holds this reservation"
                )),
                ('reserved_quantity', models.DecimalField(
                    max_digits=12, decimal_places=2, default=Decimal('0.00')
                )),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateTimeField(
                    help_text="Reservation auto-expires after this time (e.g. 30 minutes)"
                )),
                ('organization', models.ForeignKey(
                    'authenticate_app.Organization', on_delete=django.db.models.deletion.CASCADE
                )),
                ('branch', models.ForeignKey(
                    'authenticate_app.Branch', on_delete=django.db.models.deletion.CASCADE,
                    blank=True, null=True
                )),
                ('product', models.ForeignKey(
                    'product_app.Product', on_delete=django.db.models.deletion.CASCADE,
                    related_name='reservations'
                )),
            ],
            options={
                'verbose_name': 'Stock Reservation',
                'verbose_name_plural': 'Stock Reservations',
                'indexes': [
                    models.Index(fields=['product', 'organization', 'branch'], name='reservation_product_org_idx'),
                    models.Index(fields=['session_key'], name='reservation_session_idx'),
                    models.Index(fields=['expires_at'], name='reservation_expires_idx'),
                ],
            },
        ),
    ]
