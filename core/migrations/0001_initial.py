# Generated by Django 5.1.7 on 2025-06-11 07:02

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('mobile_no', models.CharField(max_length=15)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('email_verified', models.BooleanField(default=False)),
                ('email_verification_code', models.CharField(blank=True, max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='NFCCard',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('card_id', models.CharField(help_text='Unique identifier of the NFC card', max_length=255, unique=True)),
                ('secure_key', models.CharField(blank=True, help_text='Secure 16-character alphanumeric key for transactions', max_length=16, unique=True)),
                ('name', models.CharField(blank=True, help_text='Optional name for the card', max_length=100)),
                ('customer_name', models.CharField(blank=True, help_text='Name of the customer', max_length=100)),
                ('mobile_number', models.CharField(blank=True, help_text='Mobile number of the customer', max_length=15)),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, help_text='Current balance on the card', max_digits=10)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Outlet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unique_id', models.CharField(blank=True, help_text='Unique 7-digit identifier', max_length=7, unique=True)),
                ('outlet_name', models.CharField(max_length=100)),
                ('address', models.TextField(blank=True)),
                ('contact_person', models.CharField(blank=True, max_length=100)),
                ('phone_number', models.CharField(blank=True, max_length=15)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='NFCLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('card_identifier', models.CharField(help_text='Card ID at the time of scan', max_length=255)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('action', models.CharField(blank=True, help_text='Action performed with the card', max_length=100)),
                ('success', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True)),
                ('card', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.nfccard')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('outlet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.outlet')),
            ],
        ),
        migrations.CreateModel(
            name='OutletVolunteer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unique_id', models.CharField(blank=True, help_text='Unique 7-digit identifier', max_length=7, unique=True)),
                ('full_name', models.CharField(max_length=100)),
                ('contact_number', models.CharField(blank=True, max_length=15)),
                ('adhaar_card_no', models.CharField(blank=True, max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('outlet', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='volunteers', to='core.outlet')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=30)),
                ('last_name', models.CharField(blank=True, max_length=30)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('mobile_no', models.CharField(blank=True, max_length=15)),
                ('user_type', models.CharField(choices=[('admin', 'Admin'), ('outlet', 'Outlet'), ('topup_volunteer', 'Topup Volunteers'), ('outlet_volunteer', 'Outlet Volunteers')], default='outlet', max_length=16)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TopupVolunteer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unique_id', models.CharField(blank=True, help_text='Unique 7-digit identifier', max_length=7, unique=True)),
                ('full_name', models.CharField(max_length=100)),
                ('contact_number', models.CharField(blank=True, max_length=15)),
                ('adhaar_card_no', models.CharField(blank=True, max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('card_identifier', models.CharField(help_text='Card ID at the time of transaction', max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, help_text='Transaction amount', max_digits=10)),
                ('payment_method', models.CharField(choices=[('cash', 'Cash'), ('upi', 'UPI'), ('nfc', 'NFC')], default='cash', help_text='Method used for payment (Cash or UPI)', max_length=10)),
                ('previous_balance', models.DecimalField(decimal_places=2, default=0.0, help_text='Card balance before transaction', max_digits=10)),
                ('new_balance', models.DecimalField(decimal_places=2, default=0.0, help_text='Card balance after transaction', max_digits=10)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('completed', 'Completed'), ('failed', 'Failed'), ('pending', 'Pending'), ('refunded', 'Refunded')], default='pending', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('card', models.ForeignKey(blank=True, help_text='NFC card used for the transaction', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='core.nfccard')),
                ('outlet', models.ForeignKey(blank=True, help_text='Outlet where the transaction occurred', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='core.outlet')),
                ('user', models.ForeignKey(blank=True, help_text='User who processed the transaction', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Analytics',
            fields=[
            ],
            options={
                'verbose_name': 'Analytics',
                'verbose_name_plural': 'Analytics',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.transaction',),
        ),
        migrations.CreateModel(
            name='PaymentCollectionAnalytics',
            fields=[
            ],
            options={
                'verbose_name': 'Collection Analytics',
                'verbose_name_plural': 'Collection Analytics',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.transaction',),
        ),
    ]
