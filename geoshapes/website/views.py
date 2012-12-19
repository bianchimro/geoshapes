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

from shapesengine.utils import instance_dict, collect_queryset_rows, AjaxResponse
from shapesengine.shapeutils import ShapeChecker

from shapesengine.models import *

from django.core.paginator import Paginator
from website.pagination import get_page_or_1, get_paginator_page


#TODO: add data preview

#TODO: move to settings
DATASET_OBJECTS_PER_PAGE = 100

def index(request):
    
    return render_to_response('website/index.html', 
        {},
        context_instance = RequestContext(request))

def sources(request):
    
    sources = Source.objects_resolved.select_subclasses().all()
    return render_to_response('website/sources.html', 
        { 'sources' : sources },
        context_instance = RequestContext(request))


def source(request, source_id):
    
    base_source = Source.objects.get(pk=int(source_id))
    source = base_source.get_subclass()
    
    
    descriptors = source.descriptor.all()
    #load_data_url = reverse('website.views.load_data_ajax', args=(source.id,))
    
    allowed_types = json.dumps(DESCRIPTORS_TYPES_MAP.keys(),cls=DjangoJSONEncoder)
    allowed_names = json.dumps(source.get_fields())
    
    return render_to_response('website/source.html', 
        {   'source' : source, 
            'descriptors' : descriptors, 
        },
    context_instance = RequestContext(request))
    

def descriptor(request, descriptor_id):
    
    descriptor = DatasetDescriptor.objects.get(id=int(descriptor_id))
    descriptor_resource_url = reverse("website.views.descriptor_ajax", args=(descriptor_id,))
    
    base_source = Source.objects.get(pk=descriptor.source_id)
    source = base_source.get_subclass()

    descriptor_json = json.dumps(instance_dict(descriptor, recursive=True),cls=DjangoJSONEncoder)
    load_data_url = reverse('website.views.load_data_ajax', args=(descriptor.id,))
    dataset_data_url = reverse('website.views.dataset_data_ajax', args=(descriptor.id,))
    allowed_types = json.dumps(DESCRIPTORS_TYPES_MAP.keys(),cls=DjangoJSONEncoder)
    allowed_names = json.dumps(source.get_fields(),cls=DjangoJSONEncoder)
    
    return render_to_response('website/descriptor.html', 
        {   'descriptor' : descriptor, 
            'descriptor_json' : descriptor_json,
            'allowed_types': allowed_types,
            'allowed_names':allowed_names,
            'load_data_url' : load_data_url,
            'dataset_data_url' : dataset_data_url,
            'descriptor_resource_url' : descriptor_resource_url,
        },
        context_instance = RequestContext(request))






def add_source_descriptor_csv(request, source_id):

    #todo: SHOULD BE A POST!
    source = CsvSource.objects.get(pk=int(source_id))
    descriptor = DatasetDescriptor(source=source)
    descriptor.save()
    
    generate_fields_for_csv_descriptor(source, descriptor)
    
    return HttpResponseRedirect(reverse("website.views.descriptor", args=(descriptor.id,)))
    
    
    
def add_source_descriptor_shape(request, source_id):

    #todo: SHOULD BE A POST!
    source = ShapeSource.objects.get(pk=int(source_id))
    descriptor = DatasetDescriptor(source=source)
    descriptor.save()
    
    generate_fields_for_shape_descriptor(source, descriptor)
    
    return HttpResponseRedirect(reverse("website.views.descriptor", args=(descriptor.id,)))



#TODO: this has some issues when descriptor does not exist
def descriptor_ajax(request, descriptor_id=None):

    response = AjaxResponse()
    
    #post method
    if request.method == 'POST':
        if request.POST['id']:
            id_descriptor = int(request.POST['id'])
            try:
                descriptor = DatasetDescriptor.objects.get(pk = id_descriptor)
            except Exception,e:
                response.error = str(e)
                response.status = 404
                return response.as_http_response()
                
        else:
            descriptor = DatasetDescriptor()
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
                    except:
                        pass
                if not descr:
                    descr = DatasetDescriptorItem(descriptor=descriptor) 
                
                descr.name = descriptor_item['name']
                descr.type= descriptor_item['type']
                descr.save()
        
        descriptor_dict = instance_dict(descriptor, recursive=True)
        response.result = descriptor_dict

    #get method
    else:
        try:
            descriptor  = DatasetDescriptor.objects.get(pk=descriptor_id)
            descriptor_dict = instance_dict(descriptor, recursive=True, related_names=['items'], properties=['dirty', 'data_url'])
            response.result = descriptor_dict
        except Exception, e:
            response.error = str(e)
            response.status = 404

    
    return response.as_http_response()
  
    

def load_data_ajax(request, descriptor_id):
    
    response = AjaxResponse()
    try:
        descriptor = DatasetDescriptor.objects.get(pk=int(descriptor_id))
    except Exception, e:
        response.status = 404
        response.error = str(e)
        return response.as_http_response()
        
        
    out = {}
    
    if request.method == 'POST':
        try:
            descriptor.load_data()
            descriptor_dict = instance_dict(descriptor, recursive=True, properties=['metadata'])
            response.result = descriptor_dict
        except Exception, e:
            response.error = str(e)
            response.status = 500

    return response.as_http_response()



def dataset_data_ajax(request, descriptor_id):
    
    response = AjaxResponse()
    
    try:
        descriptor  = DatasetDescriptor.objects.select_related().get(id=int(descriptor_id))
    except Exception, e:
        response.status = 404
        response.error = str(e)
        return response.as_http_response()
    
    datamodel = descriptor.dymodel

    out = {}
    
    objs = datamodel.Dataset.objects.all()
    
    limit = request.GET.get('limit', None)
    offset = request.GET.get('offset', None)
    out_objs = collect_queryset_rows(objs, offset, limit)
        
    
    out = {}
    out['rows'] = out_objs
    out['descriptor'] = instance_dict(descriptor, recursive=True, related_names=['items'], properties=['metadata'])
    response.result = out
    
    return response.as_http_response()
    
    
    
def dataset_table_view(request, descriptor_id):
    
    descriptor  = DatasetDescriptor.objects.select_related().get(id=int(descriptor_id))
    datamodel = descriptor.dymodel
    
    objs = datamodel.Dataset.objects.all()
    
    paginator = Paginator(objs, DATASET_OBJECTS_PER_PAGE)
    page = get_page_or_1(request)
    dataset_page = get_paginator_page(paginator, page)
    
    return render_to_response('website/dataset_table_view.html', 
        {   'rows' : objs, 
            'meta' : descriptor.metadata,
            'descriptor':descriptor,
            'paginator_page':dataset_page
        },
        context_instance = RequestContext(request))



def load_source_data_ajax(request, source_id):

    response = AjaxResponse()
    try:
        base_source = Source.objects.get(pk=int(source_id))
        source = base_source.get_subclass()
        
        
    
        descriptor = DatasetDescriptor(source=source)
        descriptor.save()
        
        source.generate_fields_for_descriptor(descriptor)
        

        descriptor.load_data()
    
        out = {}
        out['descriptor'] = instance_dict(descriptor, recursive=True, related_names=['items'], properties=['metadata'])
        response.result = out

    except Exception, e:
        response.status = 500
        response.error = str(e)
        
    return response.as_http_response()
    
    
    


#@login_required
def add_csv_source_ajax(request):

    response = AjaxResponse()
    user = request.user
    #TODO: check if user can write    
    
    if request.method == 'POST':
    
        try:
            name = request.POST['name']
            filename = request.POST['filename']
            
            full_path = os.path.join(settings.MEDIA_ROOT, 'ajax_uploads', filename)
            part_path = os.path.join('ajax_uploads', filename)
            
            source_instance = CsvSource(name=name)
            source_instance.csv.name = part_path
            source_instance.save()
            
            
            base_render_context = {}
            """
            rendered = render_to_string('worktables/attachments_list.html', base_render_context, context_instance=RequestContext(request))
            """
            
            source_dict = instance_dict(source_instance)
            source_url = reverse("website.views.source", args=(source_instance.id,))
            out = { 'source' : source_dict, 'source_url' : source_url }
            response.result = out
            
        except Exception, e:
            response.status = 500
            response.error = str(e)
        
        
        return response.as_http_response()
        

def add_shape_source_ajax(request):

    response = AjaxResponse()
    user = request.user
    #TODO: check if user can write    
    
    if request.method == 'POST':
    
        try:
            name = request.POST['name']
            filename = request.POST['filename']
            
            full_path = os.path.join(settings.MEDIA_ROOT, 'ajax_uploads', filename)
            part_path = os.path.join('ajax_uploads', filename)
            
            #todo: check zip
            #todo: unzip to DEFAULT_SHAPES_PATH
            #todo: get new path of main shape

            checker = ShapeChecker()
            valid, msg = checker.validate(full_path)
            if not valid:
                response.status = 500
                response.error = msg
                return response.as_http_response()
            
            
            new_path = checker.handle(full_path)
            
            source_instance = ShapeSource(name=name, shape=new_path)
            source_instance.save()
            
            base_render_context = {}
            """
            rendered = render_to_string('worktables/attachments_list.html', base_render_context, context_instance=RequestContext(request))
            """
            
            source_dict = instance_dict(source_instance)
            source_url = reverse("website.views.source", args=(source_instance.id,))
            out = { 'source' : source_dict, 'source_url' : source_url }
            response.result = out
            
        except Exception, e:
            response.status = 500
            response.error = str(e)
        
    return response.as_http_response()
        


