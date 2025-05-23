# Generated by Django 5.1.7 on 2025-03-30 21:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_nfc_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='nfccard',
            name='balance',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Current balance on the card', max_digits=10),
        ),
        migrations.AddField(
            model_name='nfccard',
            name='customer_name',
            field=models.CharField(blank=True, help_text='Name of the customer', max_length=100),
        ),
        migrations.AddField(
            model_name='nfccard',
            name='mobile_number',
            field=models.CharField(blank=True, help_text='Mobile number of the customer', max_length=15),
        ),
    ]
