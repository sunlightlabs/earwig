from django.conf.urls import patterns, include, url


urlpatterns = patterns('contact.plugin.sendgrid',
    # See http://sendgrid.com/docs/API_Reference/Webhooks/event.html
    url(r'^bounce/$', 'handle_bounce'),
    # http://sendgrid.com/docs/API_Reference/Webhooks/parse.html
    url(r'^inbound/$', 'handle_inbound'),
)
