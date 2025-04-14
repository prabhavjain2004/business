# Generated by Django 5.1.7 on 2025-04-14 12:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_remove_eventstatistics_cards_issued_and_more'),
    ]

    operations = [
        # First, remove any unique_together constraints
        migrations.AlterUniqueTogether(
            name='eventoutlet',
            unique_together=None,
        ),
        
        # Then remove foreign key fields
        migrations.RemoveField(
            model_name='nfclog',
            name='event',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='event',
        ),
        migrations.RemoveField(
            model_name='eventoutlet',
            name='outlet',
        ),
        migrations.RemoveField(
            model_name='eventoutlet',
            name='event',
        ),
        
        # Finally delete the models
        migrations.DeleteModel(
            name='EventStatistics',
        ),
        migrations.DeleteModel(
            name='Event',
        ),
        migrations.DeleteModel(
            name='EventOutlet',
        ),
    ]
