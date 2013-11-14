from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^message/$', 'contact.views.create_message', name='create_message'),
)
