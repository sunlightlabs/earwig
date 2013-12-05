from django.conf.urls import patterns, include, url


urlpatterns = patterns('contact.plugin.postmark',
    # These urls need to match the webhook urls configured through the
    # postmark UI.
    url(r'^bounce/$', 'handle_bounce'),
    url(r'^inbound/$', 'handle_inbound'),
)
