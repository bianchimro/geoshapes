import uuid
import json
import csv

from django.core.exceptions import ValidationError

from django.db import models
from django.db.models.loading import cache
#from django.db.models.signals import post_save, pre_save, pre_delete, post_delete

from django.template.defaultfilters import slugify

from django.contrib.auth.models import User
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
    
from picklefield.fields import PickledObjectField

from shapesengine import utils
from shapesengine import helpers
from model_utils.managers import InheritanceManager

from shapesengine.dynamic_models import get_dataset_model
from shapesengine.mappings import *
#from shapesengine import signals


DEFAULT_APP_NAME = 'shapesengine'


#TODO: add classes for automatic creation of descriptors
#TODO: add ShapeFile source

def generate_hash_string():
    return str(uuid.uuid4).replace("-","")

class DyModel(models.Model):

    """
    Dynamic model
    """

    name = models.CharField(max_length=200, unique=True)
    alive = models.BooleanField(default=True)
    
    def __unicode__(self):
        return u'%s' % self.name
        

    def build_dataset(self, regenerate=True, notify_changes=True, reregister_in_admin=True, create_db_table=True):
        Dataset = self.get_dataset_model(regenerate=True, notify_changes=True)
        if create_db_table:        
            helpers.delete_db_table(Dataset)
            helpers.create_db_table(Dataset)
            helpers.add_necessary_db_columns(Dataset)
        
        if reregister_in_admin:
            helpers.reregister_in_admin(admin.site, Dataset)
            
        if notify_changes:
            helpers.notify_model_change(Dataset)
            
        return Dataset
        
    @property
    def Dataset(self):
        " Convenient access the relevant model class for the dataset "
        return get_dataset_model(self)

    def get_dataset_model(self, regenerate=False, notify_changes=True):
        return get_dataset_model(self, regenerate=regenerate, notify_changes=notify_changes)

    #TODO: see if it is really useful    
    def get_hash_string(self):
        """ Return a string to describe the parts of the model that are
            relevant to the generated dynamic model (the DyModel model)
        """
        # Only use the fields that are relevant
        val = [(f.name, f.type, f.args, f.kwargs) for f in self.dyfields.all()]
        return json.dumps(val)


    
class DyField(models.Model):
    """
    Dynamic field
    """

    name=models.CharField(max_length=200)
    type=models.CharField(max_length=200)
    model = models.ForeignKey(DyModel, related_name='dyfields')
    args = PickledObjectField()
    kwargs = PickledObjectField()
    
    
    def get_field_name(self):
        return slugify(self.name).replace("-", "_")
    
    
    def get_field(self):
        field_type = getattr(models, self.type)
        field = field_type(*self.args, **self.kwargs)
        return field



class Source(models.Model):

    fields = PickledObjectField()
    
    objects = models.Manager()
    objects_resolved = InheritanceManager()



class CsvSource(Source):
    
    csv = models.FileField(upload_to='csv')
    
    
    def get_fields(self):
        f = open(self.csv.path)
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        reader = csv.DictReader(f, dialect=dialect)
        fieldnames = reader.fieldnames
        f.close()
        return fieldnames
        
        
    def get_data(self):
        data = []
        f = open(self.csv.path)
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        reader = csv.DictReader(f, dialect=dialect)
        for line in reader:
            xline = {}
            for fi in line:
                fix = slugify(fi).replace("-", "_")    
                xline[fix]  = line[fi]
            data.append(xline)
        f.close()
        return data
        
    
    def save(self, *args, **kwargs):
    
        return super(CsvSource, self).save(*args, **kwargs)
        
    def __unicode__(self):
        return u"%s" % self.csv.path

    
    
class DatasetDescriptor(models.Model):
    
    name = models.CharField(max_length=200)
    source = models.ForeignKey(Source, related_name='descriptor', null=True, blank=True)


    def save(self, *args, **kwargs):
    
        if not self.name:
            self.name = self.__class__.__name__ + str(self.source.id) 
    
        
        return super(DatasetDescriptor, self).save( *args, **kwargs);
        
        
    def generate_dymodel(self):
        try:
            datamodel = DyModel.objects.get(name=self.name)
            datamodel.dyfields.all().delete()

        except:
            datamodel = DyModel(name=self.name)
            datamodel.save()
        
        fields = {}
        parsers = {}
        for descriptor_item in self.items.all():
            mapped_type =  DESCRIPTORS_TYPES_MAP[descriptor_item.type]
            field_name = str(descriptor_item.get_field_name())
            fields[field_name] = DyField(name=field_name, type=mapped_type['model'], model=datamodel, args=mapped_type['args'], kwargs=mapped_type['kwargs'])
            fields[field_name].save()
            parsers[field_name] = mapped_type['parser']

        return datamodel, fields, parsers
    
    
    
    #todo: split into simpler methods (generate_dymodel, load_data_from_source) 
    def load_data(self):
    
        datamodel, fields, parsers = self.generate_dymodel()
        Dataset = datamodel.build_dataset()
        
        actual_source = Source.objects_resolved.select_subclasses().get(pk=self.source.id)
        data = actual_source.get_data()
        
        #klass = datamodel.generate_model()
        Dataset.objects.all().delete()
        
        for d in data:
            kwargs = {}
            for f in fields:
                try:
                    strvalue = d[f]
                    value = parsers[f](strvalue)
                    kwargs[f] = value

                except Exception, e:
                    print f, e
                    kwargs[f]= None
            
            not_none_kwargs = {}
            for k in kwargs:
                v = kwargs[k]
                if v is not None:
                    not_none_kwargs[k] = v
            
            instance = Dataset(**not_none_kwargs)
            instance.save()
        
        return Dataset

DESCRIPTOR_TYPE_CHOICES = []
for x in DESCRIPTORS_TYPES_MAP:
    DESCRIPTOR_TYPE_CHOICES.append([x,x])


class DatasetDescriptorItem(models.Model):
    
    descriptor = models.ForeignKey(DatasetDescriptor, related_name = 'items')
    
    order = models.IntegerField(default=0)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=200, choices=DESCRIPTOR_TYPE_CHOICES)

    def get_field_name(self):
        return slugify(self.name).replace("-", "_")


#creating stored models
from shapesengine.dynamic_models import build_existing_dataset_models
"""
try:
    build_existing_dataset_models(DyModel)
except:
    pass    
"""