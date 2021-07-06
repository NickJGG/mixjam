# Generated by Django 3.1.4 on 2021-07-05 18:53

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0031_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='time_created',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2021, 7, 5, 18, 53, 22, 855473, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='RoomInvite',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='room_notification', to='core.notification')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invite_room', to='core.room')),
            ],
        ),
        migrations.CreateModel(
            name='FriendRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='friend_notification', to='core.notification')),
            ],
        ),
    ]
