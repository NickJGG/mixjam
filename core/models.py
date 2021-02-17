from django.contrib.auth.models import User
from django.db import models

class Room(models.Model):
    code = models.CharField(max_length = 30)
    title = models.CharField(max_length=150, default="New Room")
    leader = models.ForeignKey(User, on_delete=models.CASCADE)
    playlist_id = models.CharField(max_length = 50, null = True)
    time_created = models.DateTimeField(auto_now_add=True)
    users = models.ManyToManyField(User, related_name='users')
    active_users = models.ManyToManyField(User, related_name='active_users')

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE)
    access_token = models.CharField(max_length = 200)
    refresh_token = models.CharField(max_length = 200)