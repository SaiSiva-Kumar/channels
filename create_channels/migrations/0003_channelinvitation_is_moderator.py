# Generated by Django 5.1.3 on 2025-07-18 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('create_channels', '0002_creatorchanneldata_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='channelinvitation',
            name='is_moderator',
            field=models.BooleanField(default=False),
        ),
    ]
