from django.conf.urls import patterns, url


urlpatterns = patterns(
    'plugins.twilio_voice.views',
    url(r'^intro/(?P<contact_id>.*)/$', 'intro', name='intro'),
    url(r'^messages/(?P<contact_id>.*)/$', 'messages', name='messages'),
    url(r'^message/(?P<contact_id>.*)/(?P<sequence_id>.*)/$', 'message', name='message'),
)
