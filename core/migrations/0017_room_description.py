# Generated by Django 3.1.4 on 2021-05-10 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20210508_1558'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='description',
            field=models.CharField(default='', max_length=1000),
        ),
    ]
