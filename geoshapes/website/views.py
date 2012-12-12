# -*- coding: utf-8 -*-

import json
import os
import datetime
import mimetypes

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.utils.http import urlquote
from django.utils.encoding import smart_str

from django.contrib.auth.decorators import login_required
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.models import User, Group

from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.template import RequestContext, loader, Context

from django.core.servers.basehttp import FileWrapper
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
from django.core.files import File

from django.db.models.loading import get_model

from shapesengine.utils import instance_dict

from shapesengine.models import *

#TODO: handle errors in ajax responses
#TODO: add data preview


def index(request):
    
    return render_to_response('website/index.html', 
        {},
        context_instance = RequestContext(request))

def csvsources(request):
    
    sources = CsvSource.objects.all()
    return render_to_response('website/csvsources.html', 
        { 'sources' : sources },
        context_instance = RequestContext(request))


def csvsource(request, source_id):
    
    source = CsvSource.objects.get(pk=int(source_id))
    descriptor_resource_url = reverse('website.views.descriptor_ajax', args=(source.id,))
    load_data_url = reverse('website.views.load_data_ajax', args=(source.id,))
    
    allowed_types = json.dumps(DESCRIPTORS_TYPES_MAP.keys())
    allowed_names = json.dumps(source.get_fields())
    
    return render_to_response('website/csvsource.html', 
        {   'source' : source, 
            'descriptor_resource_url' : descriptor_resource_url, 
            'load_data_url' : load_data_url,
            'allowed_types': allowed_types,
            'allowed_names':allowed_names,
            
        },
        context_instance = RequestContext(request))


#TODO: this has some issues when descriptor does not exist
def descriptor_ajax(request, source_id):

    source = CsvSource.objects.get(pk=int(source_id))
    if request.POST:
    
        if request.POST['id']:
            id_descriptor = int(request.POST['id'])
            print "yyy", id_descriptor
            descriptor = DatasetDescriptor.objects.get(pk = id_descriptor)
        
        else:
            descriptor = DatasetDescriptor(source = source, name = "Descriptor" + str(source.id))
            print "zzzz"
            descriptor.save()
        
        try:
            for d in descriptor.items.all():
                d.delete()
        except:
            pass
        
        if 'items' in request.POST:
            descriptor_items = json.loads(request.POST['items'])
            for descriptor_item in descriptor_items:
                descr = None
                if  descriptor_item['id']:
                    try:
                        descr = DatasetDescriptorItem.objects.get(pk= descriptor_item['id'])
                        print 1
                    except:
                        pass
                        print 2
                if not descr:
                    print "3"
                    descr = DatasetDescriptorItem(descriptor=descriptor) 
                
                descr.name = descriptor_item['name']
                descr.type=descriptor_item['type']
                
                descr.save()
        
        
        out = instance_dict(descriptor, recursive=True)
    
    else:
        try:
            descriptor  = DatasetDescriptor.objects.select_related().get(source=source)
            
        except:
            
            descriptor = DatasetDescriptor(source = source)
            descriptor.save()
    
        out = instance_dict(descriptor, recursive=True)
        

    jsonOutput = json.dumps(out, cls=DjangoJSONEncoder)
    return HttpResponse(jsonOutput,  mimetype="application/json")
    

#TODO: use POST to make changes...    
def load_data_ajax(request, source_id):
    
    source = CsvSource.objects.get(pk=int(source_id))
     
    try:
        descr = DatasetDescriptor.objects.get(source=source)
        descr.load_data()
    except:
        raise
        
    out = {}
    if request.POST:
        print 1
    
    

    jsonOutput = json.dumps(out, cls=DjangoJSONEncoder)
    return HttpResponse(jsonOutput,  mimetype="application/json")
    