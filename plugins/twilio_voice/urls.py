from django.conf.urls import patterns, url


urlpatterns = patterns(
    'plugins.twilio_voice.views',
    url(r'^call/(?P<contact_id>.*)/$', 'call', name='call'),
)
