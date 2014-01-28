from django.conf import settings
from django.contrib import admin
from django.conf.urls import patterns, include, url


admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^', include('contact.urls')),
    url(r'^plugins/postmark/', include('plugins.postmark.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns(
        '',
        url(r'^admin/', include(admin.site.urls)),
    )
