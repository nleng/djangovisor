"""djangovisor URL Configuration

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

urlpatterns = [
    url(r'^$', 'djangovisor.views.dashboard', name='dashboard'),
    url(r'^dashboard/$', 'djangovisor.views.dashboard', name='dashboard'),
    url(r'^collector$', 'djangovisor.views.collector', name='collector'),
    url(r'^server/(?P<server_id>\d+)/$', 'djangovisor.views.server', name='server'),
    url(r'^server/(?P<server_id>\w+)/process/(?P<process_name>[^/]+)/$', 'djangovisor.views.process', name='process'),
    url(r'^process_action/(?P<server_id>\d+)/$', 'djangovisor.views.process_action', name='process_action'),
    url(r'^confirm_delete/(?P<server_id>\d+)/$', 'djangovisor.views.confirm_delete', name='confirm_delete'),
    url(r'^delete_server/(?P<server_id>\d+)/$', 'djangovisor.views.delete_server', name='delete_server'),

    # urls for ajax calls
    url(r'^load_server_data/(?P<server_id>\d+)/$', 'djangovisor.views.load_server_data', name='load_server_data'),
    url(r'^load_process_data/(?P<server_id>\d+)/(?P<process_name>[^/]+)/$', 'djangovisor.views.load_process_data', name='load_process_data'),
    url(r'^load_dashboard_table/$', 'djangovisor.views.load_dashboard_table', name='load_dashboard_table'),
    url(r'^load_server_table/(?P<server_id>\d+)/$', 'djangovisor.views.load_server_table', name='load_server_table'),
    url(r'^load_process_table/(?P<server_id>\d+)/(?P<process_name>[^/]+)/$', 'djangovisor.views.load_process_table', name='load_process_table'),
]
