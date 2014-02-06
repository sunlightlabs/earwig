from django.conf.urls import patterns, url


urlpatterns = patterns('plugins.twilio_sms.views',
    url(r'^text/(?P<contact_id>.*)/$', 'text', name='text'),
)
