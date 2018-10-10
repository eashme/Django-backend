"""Hellocial URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url
from apps.users.views import UserInfoView, CheckCodeView, LoginView, LoginOutView, RegisterView, UserRelationView, \
    UserSlaveView, UserSlaveDelView, UserSlaveEditView, AppLogin1View, AppLogin2View, UserFornumView, PasswordView

urlpatterns = [
    url(r'^login$', LoginView.as_view()),
    url(r'^checkcode$', CheckCodeView.as_view()),
    url(r'^loginout$', LoginOutView.as_view()),
    url(r'^register$', RegisterView.as_view()),
    url(r'^relations$', UserRelationView.as_view()),
    url(r'^slaves$', UserSlaveView.as_view()),
    url(r'^slaves/remove$', UserSlaveDelView.as_view()),
    url(r'^edit', UserSlaveEditView.as_view()),
    url(r'^app/login$', AppLogin1View.as_view()),
    url(r'^app/login2$', AppLogin2View.as_view()),
    url(r'^pwd$', PasswordView.as_view()),
    url(r'^user_fornum', UserFornumView.as_view()),
    url(r'^$', UserInfoView.as_view())
]
