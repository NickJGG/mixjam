# Generated by Django 3.1.4 on 2021-05-05 19:39

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0012_auto_20210407_1803'),
    ]

    operations = [
        migrations.AlterField(
            model_name='room',
            name='active_users',
            field=models.ManyToManyField(blank=True, related_name='active_users', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='room',
            name='playlist_image_url',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='room',
            name='users',
            field=models.ManyToManyField(blank=True, related_name='users', to=settings.AUTH_USER_MODEL),
        ),
    ]