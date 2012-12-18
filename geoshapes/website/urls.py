from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('website.views',



    url(r'^sources/$', 'sources'),
    url(r'^add_csv_source_ajax/$', 'add_csv_source_ajax'),
    url(r'^add_shape_source_ajax/$', 'add_shape_source_ajax'),        
        
    url(r'^source/(?P<source_id>\d+)/$', 'source', name="source"),
    url(r'^load_source_data_ajax/(?P<source_id>\d+)/$', 'load_source_data_ajax', name="load_source_data_ajax"),
    url(r'^descriptor/(?P<descriptor_id>\d+)/$', 'descriptor', name="descriptor"),
    url(r'^add_source_descriptor_csv/(?P<source_id>\d+)/$', 'add_source_descriptor_csv', name="add_source_descriptor_csv"),
    url(r'^descriptor_ajax/(?P<descriptor_id>\d+)/$', 'descriptor_ajax', name="descriptor_ajax"),

    url(r'^dataset_data_ajax/(?P<descriptor_id>\d+)/$', 'dataset_data_ajax', name="dataset_data_ajax"),
    url(r'^dataset_table_view/(?P<descriptor_id>\d+)/$', 'dataset_table_view', name="dataset_table_view"),
    
    url(r'^load_data_ajax/(?P<descriptor_id>\d+)/$', 'load_data_ajax', name="load_data_ajax"),

    url(r'^$', 'index'),
    



)