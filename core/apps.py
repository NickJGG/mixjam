from django.apps import AppConfig

class CoreConfig(AppConfig):
    name = 'core'

class StartupConfig(AppConfig):
    name = 'core'
    verbose_name = "MixJam"

    def ready(self):
        from .models import UserProfile

        for user in UserProfile.objects.all():
            user.online_count = 0
            user.save()