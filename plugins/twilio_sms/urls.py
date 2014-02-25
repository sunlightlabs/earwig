from django.conf.urls import patterns, url


urlpatterns = patterns(
    'plugins.twilio_sms.views',
    url(r'^text/$', 'text', name='text'),
)
