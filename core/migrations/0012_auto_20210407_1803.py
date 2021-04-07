# Generated by Django 3.1.4 on 2021-04-07 22:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_auto_20210407_1755'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfilePicture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.AddField(
            model_name='userprofile',
            name='icon_image',
            field=models.CharField(choices=[('baby-yoda', 'Baby Yoda'), ('brutus', 'Brutus'), ('elf', 'Elf'), ('futurama-bender', 'Bender'), ('scream', 'Scream')], default='baby-yoda', max_length=100),
        ),
    ]
