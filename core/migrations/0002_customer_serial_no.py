# Generated by Django 5.1.7 on 2025-06-19 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='serial_no',
            field=models.PositiveIntegerField(blank=True, help_text='Auto-incrementing serial number starting from 1000', null=True, unique=True),
        ),
    ]
