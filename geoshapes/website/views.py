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
#TODO use source_class


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
    
    source = Source.objects_resolved.select_subclasses().select_related().get(pk=int(source_id))
    descriptors = source.descriptor.all()
    #load_data_url = reverse('website.views.load_data_ajax', args=(source.id,))
    
    allowed_types = json.dumps(DESCRIPTORS_TYPES_MAP.keys())
    allowed_names = json.dumps(source.get_fields())
    
    return render_to_response('website/source.html', 
        {   'source' : source, 
            'descriptors' : descriptors, 
        },
    context_instance = RequestContext(request))
    

def descriptor(request, descriptor_id):
    
    descriptor = DatasetDescriptor.objects.get(id=int(descriptor_id))
    descriptor_resource_url = reverse("website.views.descriptor_ajax", args=(descriptor_id,))
    
    source = Source.objects_resolved.select_subclasses().get(id=descriptor.source.id)

    descriptor_json = json.dumps(instance_dict(descriptor, recursive=True),cls=DjangoJSONEncoder)
    load_data_url = reverse('website.views.load_data_ajax', args=(descriptor.id,))
    dataset_data_url = reverse('website.views.dataset_data_ajax', args=(descriptor.id,))
    allowed_types = json.dumps(DESCRIPTORS_TYPES_MAP.keys())
    allowed_names = json.dumps(source.get_fields())
    
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



#todo: make a class, move elsewhere
from shapesengine.inspectors.csvinspector import CSVInspector
from shapesengine.inspectors.shapesinspector import ShapesInspector

def generate_fields_for_csv_descriptor(source, descriptor):
    for d in descriptor.items.all():
        d.delete()
        
    inspector = CSVInspector(source.csv.path)
    inspector.analyze()
    generate_fields_from_meta(descriptor, inspector.meta)

def generate_fields_for_shape_descriptor(source, descriptor):
    for d in descriptor.items.all():
        d.delete()
        
    inspector = ShapesInspector(source.csv.path)
    inspector.analyze()
    generate_fields_from_meta(descriptor, inspector.meta)


def generate_fields_from_meta(descriptor, meta):
    for field_name in meta:
        field = meta[field_name]
        item = DatasetDescriptorItem(descriptor=descriptor, name=field_name, type=field['type'])
        item.save()




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

    descriptor = DatasetDescriptor.objects.get(pk=int(descriptor_id))
    if request.method == 'POST':
        if request.POST['id']:
            id_descriptor = int(request.POST['id'])
            descriptor = DatasetDescriptor.objects.get(pk = id_descriptor)
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
        
        
        out = instance_dict(descriptor, recursive=True)
    
    else:
        try:
            descriptor  = DatasetDescriptor.objects.get(pk=descriptor_id)
        except:
            raise Http404
                
        out = instance_dict(descriptor, recursive=True, related_names=['items'], properties=['dirty', 'data_url'])
    #todo: handle errors
    jsonOutput = json.dumps(out, cls=DjangoJSONEncoder)
    return HttpResponse(jsonOutput,  mimetype="application/json")
    

def load_data_ajax(request, descriptor_id):
    
    descriptor = DatasetDescriptor.objects.get(pk=int(descriptor_id))
        
    out = {}
    
    if request.method == 'POST':
        descriptor.load_data()
        
    out = instance_dict(descriptor, recursive=True, properties=['metadata'])
    
    #todo: return errors or some response ...
    jsonOutput = json.dumps(out, cls=DjangoJSONEncoder)
    return HttpResponse(jsonOutput,  mimetype="application/json")



def dataset_data_ajax(request, descriptor_id):
    
    descriptor  = DatasetDescriptor.objects.select_related().get(id=int(descriptor_id))
    datamodel = descriptor.dymodel

    out = {}
    out_objs = []    
    objs = datamodel.Dataset.objects.all()
    
    limit = getattr(request.GET, 'limit', None)
    offset = getattr(request.GET, 'limit', None)
    
    #basic limit and offset    
    if limit and offset:
        objs = objs[int(offset) : int(limit)]
    else:
        if limit:
            objs = objs[:int(limit)]
        if offset:
            objs = objs[int(offset):]
    
    for o in objs:
        out_objs.append(instance_dict(o, recursive=True))
        
    
    out['rows'] = out_objs
    out['descriptor'] = instance_dict(descriptor, recursive=True, related_names=['items'], properties=['metadata'])
    
    jsonOutput = json.dumps(out, cls=DjangoJSONEncoder)
    return HttpResponse(jsonOutput,  mimetype="application/json")    
    
    
def dataset_table_view(request, descriptor_id):
    
    descriptor  = DatasetDescriptor.objects.select_related().get(id=int(descriptor_id))
    datamodel = descriptor.dymodel

    out = {}
    out_objs = []    
    objs = datamodel.Dataset.objects.all()
    
    limit = getattr(request.GET, 'limit', None)
    offset = getattr(request.GET, 'limit', None)
    
    #basic limit and offset    
    if limit and offset:
        objs = objs[int(offset) : int(limit)]
    else:
        if limit:
            objs = objs[:int(limit)]
        if offset:
            objs = objs[int(offset):]
    
    for o in objs:
        out_objs.append(instance_dict(o, recursive=True))
    
    
    return render_to_response('website/dataset_table_view.html', 
        {   'rows' : out_objs, 
            'meta' : descriptor.metadata,
            'descriptor':descriptor
        },
    context_instance = RequestContext(request))





def load_source_data_ajax(request, source_id):

    #todo: SHOULD BE A POST!
    source = Source.objects_resolved.select_subclasses().get(pk=int(source_id))
    descriptor = DatasetDescriptor(source=source)
    descriptor.save()
    
    generate_fields_for_csv_descriptor(source, descriptor)

    descriptor.load_data()
    
    out = {}
    out['descriptor'] = instance_dict(descriptor, recursive=True, related_names=['items'], properties=['metadata'])
    
    jsonOutput = json.dumps(out, cls=DjangoJSONEncoder)
    return HttpResponse(jsonOutput,  mimetype="application/json")






#@login_required
def add_source_ajax(request):
    user = request.user
    #TODO: check if user can write    
    
    
    if request.method == 'POST':
        print "1"
       
        print "2"
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
        
        jsonOutput = json.dumps(out, cls=DjangoJSONEncoder)
        return HttpResponse(jsonOutput,  mimetype="application/json")
        
