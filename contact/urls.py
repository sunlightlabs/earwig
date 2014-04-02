from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^sender/$', 'contact.views.create_sender', name='create_sender'),
    url(r'^message/$', 'contact.views.create_message', name='create_message'),
    url(r'^message/(?P<message_id>[0-9a-f]{32})/$', 'contact.views.get_message',
        name='get_message'),

    # other views
    url(r'^flag/(?P<transaction>.*)/(?P<secret>.*)/$', 'contact.views.flag', name='flag'),
    url(r'^feedback/(?P<attempt_id>.*)/$',
            'contact.views.submit_feedback', name='feedback'),
)
