from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^message/$', 'contact.views.create_message', name='create_message'),
    url(r'^message/(?P<message_id>\d+)/$', 'contact.views.get_message', name='get_message'),
)
