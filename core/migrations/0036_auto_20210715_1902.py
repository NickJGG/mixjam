# Generated by Django 3.1.4 on 2021-07-15 23:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_auto_20210714_1117'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='image_large',
            field=models.ImageField(blank=True, null=True, upload_to='large/'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='image_medium',
            field=models.ImageField(blank=True, null=True, upload_to='medium/'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='image_small',
            field=models.ImageField(blank=True, null=True, upload_to='small/'),
        ),
    ]