from django.conf.urls import patterns, url, include


urlpatterns = patterns(
    '',

    url(r'^statistics/overview/$', 'contact.admin.views.statistics.overview',
        name='overview'),
    url(r'^statistics/overview/(?P<template>.*)$',
        'contact.admin.views.statistics.overview_template',
        name='overview_template'),
)
