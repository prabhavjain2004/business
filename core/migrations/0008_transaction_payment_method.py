# Generated by Django 5.1.7 on 2025-03-31 01:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_transaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='payment_method',
            field=models.CharField(choices=[('cash', 'Cash'), ('upi', 'UPI')], default='cash', help_text='Method used for payment (Cash or UPI)', max_length=10),
        ),
    ]
