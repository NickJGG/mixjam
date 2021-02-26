from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Room(models.Model):
    code = models.CharField(max_length = 30)
    title = models.CharField(max_length=150, default="New Room")
    leader = models.ForeignKey(User, on_delete=models.CASCADE)
    time_created = models.DateTimeField(auto_now_add=True)
    playlist_id = models.CharField(max_length = 50, null = True)
    offset = models.IntegerField(default = 0, blank = True)
    playing = models.BooleanField(default = False, blank = True)
    progress = models.IntegerField(default = 0, blank = True)
    progress_time = models.DateTimeField(null = True, blank = True)
    users = models.ManyToManyField(User, related_name='users')
    active_users = models.ManyToManyField(User, related_name='active_users')

    def __str__(self):
        return self.code

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE)
    access_token = models.CharField(max_length = 200)
    refresh_token = models.CharField(max_length = 200)

    def __str__(self):
        return self.user.username