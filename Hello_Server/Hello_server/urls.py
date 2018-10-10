"""Hellocial_0_1 URL Configuration

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
from django.conf.urls import include, url
from django.contrib import admin
from utils.util_view import RedirctView,CheckLoginView,ServiceDatetimeView
from apps.users.views import SearchResultView

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^search$',SearchResultView.as_view()),
    url(r'^users/',include('apps.users.urls')),
    url(r'^redirct',RedirctView.as_view()),
    url(r'^isLogin$',CheckLoginView.as_view()),
    url(r'^script/',include('apps.scripts.urls')),
    url(r'^now$',ServiceDatetimeView.as_view()),
    url(r'^products/',include('apps.products.urls')),
    url(r'^',include('apps.pub_metarial.urls'))
]
