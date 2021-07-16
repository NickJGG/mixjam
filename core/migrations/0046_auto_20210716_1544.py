# Generated by Django 3.1.4 on 2021-07-16 19:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0045_auto_20210716_1542'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfilePicture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('small', models.ImageField(blank=True, null=True, upload_to='small')),
                ('medium', models.ImageField(blank=True, null=True, upload_to='medium')),
                ('large', models.ImageField(blank=True, null=True, upload_to='large')),
            ],
        ),
        migrations.RemoveField(
            model_name='profilepicture',
            name='large',
        ),
        migrations.RemoveField(
            model_name='profilepicture',
            name='medium',
        ),
        migrations.RemoveField(
            model_name='profilepicture',
            name='small',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='picture',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='profile_picture', to='core.profilepicture'),
        ),
    ]