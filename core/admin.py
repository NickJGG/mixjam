from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(Room)
admin.site.register(Playlist)
admin.site.register(UserProfile)
admin.site.register(Notification)
admin.site.register(RoomInvite)
admin.site.register(FriendRequest)