from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('website.views',



    url(r'^csvsources/$', 'csvsources'),
    url(r'^csvsource/(?P<source_id>\d+)/$', 'csvsource', name="csvsource"),
    url(r'^descriptor/(?P<descriptor_id>\d+)/$', 'descriptor', name="descriptor"),
    url(r'^add_source_descriptor/(?P<source_id>\d+)/$', 'add_source_descriptor', name="add_source_descriptor"),
    url(r'^descriptor_ajax/(?P<descriptor_id>\d+)/$', 'descriptor_ajax', name="descriptor_ajax"),

    url(r'^dataset_data_ajax/(?P<descriptor_id>\d+)/$', 'dataset_data_ajax', name="dataset_data_ajax"),
    url(r'^dataset_table_view/(?P<descriptor_id>\d+)/$', 'dataset_table_view', name="dataset_table_view"),
    
    url(r'^load_data_ajax/(?P<descriptor_id>\d+)/$', 'load_data_ajax', name="load_data_ajax"),

    url(r'^$', 'index'),
    



)