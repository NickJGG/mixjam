# Generated by Django 3.1.4 on 2021-05-13 23:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_auto_20210512_1907'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='most_recent_room',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='most_recent_name', to='core.room'),
        ),
    ]
