# Generated by Django 3.1.4 on 2021-05-07 19:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_playlist'),
    ]

    operations = [
        migrations.AddField(
            model_name='playlist',
            name='last_song_end',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
