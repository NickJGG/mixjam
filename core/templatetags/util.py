from django import template
register = template.Library()

from core.models import *

@register.simple_tag
def get_rooms(user):
    return Room.objects.filter(users = user).all()