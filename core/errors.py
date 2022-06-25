from django.shortcuts import render


errors = {
    'no_link': {
        'error_title': 'Spotify Link Error',
        'error_message': 'No Spotify account linked',
        'error_code': 100
    },
    'non_member': {
        'error_title': 'Room Error',
        'error_message': 'You are not a member of this room',
        'error_code': 101
    },
    'invalid_invite': {
        'error_title': 'Invite Error',
        'error_message': 'Invite code invalid',
        'error_code': 102
    },
    'expired_invite': {
        'error_title': 'Invite Error',
        'error_message': 'Invite code expired',
        'error_code': 103
    },
    'invalid_room': {
        'error_title': 'Invite Error',
        'error_message': 'Room does not exist',
        'error_code': 104
    }
}

def error(request, error_str):
    return render(request, 'core/error.html', errors[error_str])

def no_link(request):
    return error(request, 'no_link')

def non_member(request):
    return error(request, 'non_member')

def invalid_invite(request):
    return error(request, 'invalid_invite')

def expired_invite(request):
    return error(request, 'expired_invite')

def invalid_room(request):
    return error(request, 'invalid_room')