from django.conf.urls import patterns, url


urlpatterns = patterns(
    'plugins.postmark.views',
    # These urls need to match the webhook urls configured through the postmark UI.
    url(r'^bounce/$', 'handle_bounce', name='postmark.handle_bounce'),
    url(r'^inbound/$', 'handle_inbound', name='postmark.handle_inbound'),
)
