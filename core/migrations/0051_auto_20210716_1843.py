# Generated by Django 3.1.4 on 2021-07-16 22:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0050_userprofile_picture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='room',
            name='banner_color',
            field=models.CharField(blank=True, default='ec4a4e', max_length=6, null=True),
        ),
    ]
