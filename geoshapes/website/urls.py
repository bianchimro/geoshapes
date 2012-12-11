from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('website.views',

    url(r'^descriptor_ajax/(?P<source_id>\d+)/$', 'descriptor_ajax', name="descriptor_ajax"),
    url(r'^load_data_ajax/(?P<source_id>\d+)/$', 'load_data_ajax', name="load_data_ajax"),
    url(r'^csvsource/(?P<source_id>\d+)/$', 'csvsource', name="csvsource"),
    url(r'^csvsources/$', 'csvsources'),
    url(r'^$', 'index'),


)