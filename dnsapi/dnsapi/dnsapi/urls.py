from django.conf.urls import patterns, include, url
from django.contrib import admin
from dnsapi.views import get_request
urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'dnsapi.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^nsupdate$', get_request),
)
