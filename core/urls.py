"""syncify URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

import core

from . import views

urlpatterns = [
    path('', views.index, name = 'index'),
    path('callback/', views.callback, name = 'callback'),

    path('r/<str:room_code>/', views.room, name = 'room'),
    path('i/<str:invite_code>/', views.invite, name = 'invite'),

    path('account/', views.account, name = 'account'),
    path('login/', views.login, name = 'login'),
    path('logout/', views.logout, name = 'logout'),
    path('register/', views.register, name = 'register'),
    
    path('reset/', views.password_reset, name = 'password_reset'),
    path('reset/done', views.password_done, name = 'password_done'),
    path('reset/confirm', views.password_confirm, name = 'password_confirm'),
    path('reset/complete', views.password_complete, name = 'password_complete'),

    path('.well-known/pki-validation/8A3D973566FBB24256364C68D5B03A1F.txt/', views.ssl_validation, name = 'ssl_validation'),
]
