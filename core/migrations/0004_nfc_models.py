# Generated manually

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('core', '0003_alter_profile_user_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='NFCCard',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('card_id', models.CharField(help_text='Unique identifier of the NFC card', max_length=255, unique=True)),
                ('name', models.CharField(blank=True, help_text='Optional name for the card', max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
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
                ('outlet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.outlet')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
        ),
    ]
