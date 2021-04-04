# Generated by Django 3.1.4 on 2021-02-23 01:44

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_room_playlist_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='offset',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='room',
            name='playing',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AddField(
            model_name='room',
            name='progress',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='room',
            name='progress_time',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2021, 2, 23, 1, 44, 11, 949948, tzinfo=utc), null=True),
        ),
    ]