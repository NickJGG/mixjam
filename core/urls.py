from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, include

import core

from . import views

urlpatterns = [
    path('', views.index, name = 'index'),
    path('callback/', views.callback, name = 'callback'),

    path('r/<str:room_code>/', views.room, name = 'room'),
    path('i/<str:invite_code>/', views.invite, name = 'invite'),

    path('notification/', views.notification, name = 'notification'),
    path('friend/request/', views.request_friend, name = 'request_friend'),
    path('friend/remove/', views.remove_friend, name = 'remove_friend'),
    path('room/invite/', views.room_invite, name = 'room_invite'),
    path('room/kick/', views.room_kick, name = 'room_kick'),

    path('account/', views.account, name = 'account'),
    path('account/edit/', views.account_edit, name = 'account_edit'),
    path('login/', views.login, name = 'login'),
    path('logout/', views.logout, name = 'logout'),
    path('register/', views.register, name = 'register'),
    
    path('password_reset/', views.password_reset, name = 'password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name = 'core/password_reset/password_reset_done.html'), name = 'password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name = 'core/password_reset/password_reset_confirm.html'), name = 'password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name = 'core/password_reset/password_reset_complete.html'), name = 'password_reset_complete'),

    path('.well-known/pki-validation/2C3B9EAF7A93B50467ACD8A6FB6C36AE.txt/', views.ssl_validation, name = 'ssl_validation'),
]