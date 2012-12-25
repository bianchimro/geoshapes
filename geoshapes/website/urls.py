from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('website.views',



    url(r'^private/$', 'private'),
    url(r'^login/$', 'login'),


    url(r'^sources/$', 'sources'),
    url(r'^add_csv_source_ajax/$', 'add_csv_source_ajax'),
    url(r'^add_shape_source_ajax/$', 'add_shape_source_ajax'),        
        
    url(r'^source/(?P<source_id>\d+)/$', 'source', name="source"),
    url(r'^load_source_data_ajax/(?P<source_id>\d+)/$', 'load_source_data_ajax', name="load_source_data_ajax"),
    

    url(r'^descriptor/(?P<descriptor_id>\d+)/$', 'descriptor', name="descriptor"),
    
    url(r'^descriptors/$', 'descriptors', name='descriptors'),    
    url(r'^descriptoritems_order_ajax/$', 'descriptoritems_order_ajax', name='descriptoritems_order_ajax'),    
    
    url(r'^add_source_descriptor_csv/(?P<source_id>\d+)/$', 'add_source_descriptor_csv', name="add_source_descriptor_csv"),
    url(r'^add_source_descriptor_shape/(?P<source_id>\d+)/$', 'add_source_descriptor_shape', name="add_source_descriptor_shape"),
    
    url(r'^descriptor_ajax/(?P<descriptor_id>\d+)/$', 'descriptor_ajax', name="descriptor_ajax"),
    url(r'^drop_descriptor_ajax/(?P<descriptor_id>\d+)/$', 'drop_descriptor_ajax', name="drop_descriptor_ajax"),    

    url(r'^dataset_data_ajax/(?P<descriptor_id>\d+)/$', 'dataset_data_ajax', name="dataset_data_ajax"),
    url(r'^dataset_geodata_ajax/(?P<descriptor_id>\d+)/$', 'dataset_geodata_ajax', name="dataset_geodata_ajax"),  
    
    url(r'^dataset_geodata_ajax_chunks/(?P<descriptor_id>\d+)/$', 'dataset_geodata_ajax_chunks', name="dataset_geodata_ajax_chunks"),      
    
    url(r'^dataset_table_view/(?P<descriptor_id>\d+)/$', 'dataset_table_view', name="dataset_table_view"),
    url(r'^dataset_map_view/(?P<descriptor_id>\d+)/$', 'dataset_map_view', name="dataset_map_view"),
    
    url(r'^load_data_ajax/(?P<descriptor_id>\d+)/$', 'load_data_ajax', name="load_data_ajax"),

    url(r'^$', 'index'),
    



)