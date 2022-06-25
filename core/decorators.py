from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render

from functools import wraps

from . import errors

# views.py
def authorization_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.userprofile.authorized:
            return function(request, *args, **kwargs)
        else:
            return errors.no_link(request)

    return wrap