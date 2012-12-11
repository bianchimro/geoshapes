from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('shapesengine.views',
    
    url(r'^ajax-upload$', 'import_uploader', name="my_ajax_upload"),

)