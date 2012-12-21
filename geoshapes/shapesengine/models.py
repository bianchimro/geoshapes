import uuid
import json
import csv
import os

from django.core.exceptions import ValidationError
from django.conf import settings

#from django.db import models
from django.contrib.gis.db import models
from django.db.models.loading import cache
#from django.db.models.signals import post_save, pre_save, pre_delete, post_delete

from django.template.defaultfilters import slugify

from django.contrib.auth.models import User
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models.loading import get_model
    
from picklefield.fields import PickledObjectField

from shapesengine import utils
from shapesengine import helpers
from model_utils.managers import InheritanceManager

from shapesengine.dynamic_models import get_dataset_model
from shapesengine.mappings import *
#from shapesengine import signals

from shapesengine.inspectors.shapesinspector import ShapesInspector
from shapesengine.inspectors.csvinspector import CSVInspector
#from shapesengine.inspectors.helpers import clean_field_name


DEFAULT_APP_NAME = 'shapesengine'
DEFAULT_SHAPES_PATH = os.path.join(settings.MEDIA_ROOT, "shapes_uploads")


#TODO: add classes for automatic creation of descriptors
#TODO: add ShapeFile source

def generate_hash_string():
    return str(uuid.uuid4).replace("-","")




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
        
    inspector = ShapesInspector(source.shape)
    inspector.analyze()
    generate_fields_from_meta(descriptor, inspector.meta)



def generate_fields_from_meta(descriptor, meta):
    for field_name in meta:
        field = meta[field_name]
        item = DatasetDescriptorItem(descriptor=descriptor, name=field_name, type=field['type'])
        item.save()

#todo: make a class, move elsewhere #end








class DyModel(models.Model):

    """
    Dynamic model
    """

    alive = models.BooleanField(default=True)
    has_table = models.BooleanField(default=False)
    hash_value = models.TextField(null=True, blank=True)
    
    descriptor = models.OneToOneField("DatasetDescriptor", related_name="dymodel")
    
    
    def __unicode__(self):
        return u'DyModel: %s' % self.id
        

    def build_dataset(self, regenerate=True, notify_changes=True, reregister_in_admin=True, create_db_table=True):
        
        Dataset = self.get_dataset_model(regenerate=True, notify_changes=True)
        
        if create_db_table:        
            helpers.delete_db_table(Dataset)
            helpers.create_db_table(Dataset)
            helpers.add_necessary_db_columns(Dataset)
            
            self.has_table = True
            self.hash_value = self.get_hash_string()
            self.save()
        
        if reregister_in_admin:
            helpers.reregister_in_admin(admin.site, Dataset)
            
        if notify_changes:
            helpers.notify_model_change(Dataset)
            
        return Dataset
        
    @property
    def Dataset(self):
        " Convenient access the relevant model class for the dataset "
        return get_dataset_model(self)

    @property
    def dirty(self):
        current_hash = self.get_hash_string()
        return current_hash != self.hash_value
    
    
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

    
    @property
    def has_geo_fields(self):
        for f in self.dyfields.all():
            if f.type in utils.GEOM_FIELDS:
                return True
        return False

    @property
    def non_geo_fields(self):
        out = []
        for f in self.dyfields.all():
            if f.type not in utils.GEOM_FIELDS:
                out.append(f.get_field_name())
        return out

        
    
    
class DyField(models.Model):
    """
    Dynamic field
    """

    name=models.CharField(max_length=200)
    label=models.CharField(max_length=200)
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

    def save(self, *args, **kwargs):
        if not self.label:
            self.label=self.name
        return super(DyField, self).save(*args, **kwargs)
    

class Source(models.Model):

    name = models.CharField(max_length=200, null=True, blank=True)
    source_class = models.CharField(max_length=200, null=True, blank=True, editable=False)
    objects = models.Manager()
    objects_resolved = InheritanceManager()
    
    
    def get_subclass(self):
        mod = get_model('shapesengine', self.source_class)
        return mod.objects.select_related().get(source_ptr__id = self.id)
        
    
    @property
    def default_name(self):
        return None
        
    @property
    def has_descriptors(self):
        return bool(self.descriptor)
        
    @property
    def num_descriptors(self):
        if self.has_descriptors:
            return self.descriptor.all().count()
        return 0

    @property
    def first_descriptor(self):
        if self.descriptor:
            x = self.descriptor.all()
            try:
                return x[0]
            except:
                return None
        

    @property
    def has_descriptor_with_table(self):
        desc = self.first_descriptor
        if not desc:
            return False
        return desc.has_dymodel_with_table
    
    
    def save(self, *args, **kwargs):
        
        self.source_class = self.__class__.__name__
        
        if not self.name:
            default_name = self.default_name
            if default_name:
                self.name = self.default_name
        
        return super(Source, self).save(*args, **kwargs)


#TODO: use inspector here!
class CsvSource(Source):
    
    csv = models.FileField(upload_to='csv')

    source_type = "csv"
    source_type_label = "Csv file"
    
    _inspector_meta = None
    _csv_inspector = None

    @property
    def default_name(self):
        return os.path.split(self.csv.name)[-1]

    @property
    def inspector(self):
        if self._csv_inspector:
            return self._csv_inspector
        self._csv_inspector = CSVInspector(self.csv.name) 
        return self._csv_inspector
    
    @property
    def inspectormeta(self):
        if self._inspector_meta:
            return self._inspector_meta
        
        self.inspector.analyze()
        self._inspector_meta = self.inspector.meta
        return self._inspector_meta
    
        
    def get_fields(self):
        return self.inspectormeta.keys()
        
    """    
    def get_fields(self):
    
        f = open(self.csv.path)
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        reader = csv.DictReader(f, dialect=dialect)
        fieldnames = reader.fieldnames
        f.close()
        return fieldnames
    """
    
    def get_data(self):
        return self.inspector.getDataAsDict()
         
    """    
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
    """    
    
    def save(self, *args, **kwargs):
    
        #self.source_class = self.__class__.__name__
        return super(CsvSource, self).save(*args, **kwargs)
        
        
    def __unicode__(self):
        return u"%s" % self.csv.path
        
        
    def generate_fields_for_descriptor(self, descriptor):
        return generate_fields_for_csv_descriptor(self, descriptor)
        
        

class ShapeSource(Source):
    
    source_type = "shp"
    source_type_label = "Shapefile"
    
    #TODO: move to FilePathField
    #shape = models.CharField(max_length=200)
    shape = models.CharField(max_length=300)
    
    _inspector_meta = None
    _shapes_inspector = None
    
    @property
    def default_name(self):
        return os.path.split(self.shape)[-1]
    
    @property
    def inspector(self):
        if self._shapes_inspector:
            return self._shapes_inspector
        self._shapes_inspector = ShapesInspector(self.shape) 
        return self._shapes_inspector
    
    @property
    def meta(self):
        if self._inspector_meta:
            return self._inspector_meta
            
        self.inspector.analyze()
        self._inspector_meta = self.inspector.meta
        return self._inspector_meta
    

    def get_fields(self):
        return self.meta.keys()
    
    
    def get_data(self):
        return self.inspector.getDataAsDict()
        
    def generate_fields_for_descriptor(self, descriptor):
        return generate_fields_for_shape_descriptor(self, descriptor)
    
    
class DatasetDescriptor(models.Model):
    
    name = models.CharField(max_length=200, default="Descriptor")
    source = models.ForeignKey(Source, related_name='descriptor', null=True, blank=True)
    
    
    def save(self, *args, **kwargs):
        return super(DatasetDescriptor, self).save( *args, **kwargs);
          
    @property
    def data_url(self):
        return 1
        
    @property    
    def has_dymodel(self):
        return bool(self.dymodel)

    @property
    def has_dymodel_with_table(self):
        return bool(self.dymodel) and self.dymodel.has_table
    
        
    @property
    def metadata(self):
        if self.dymodel:
            meta = self.generate_meta()

            out = { 'fields'  : {}}
            
            for f in meta['fields']:
                name = f
                inst = meta['fields'][f]
                out['fields'][name] = inst['type']
            
            out['geo_fields'] = meta ['geo_fields']
            out['non_geo_fields'] = meta ['non_geo_fields']
            return out
        return None

    def generate_dymodel(self):
        try:
            datamodel = self.dymodel
            datamodel.dyfields.all().delete()
        except:
            datamodel = DyModel(descriptor=self)
            datamodel.save()
        
        return datamodel
        
    
    def generate_dymodel_fields(self):
        datamodel = self.dymodel
            
        fields = {}
        for descriptor_item in self.items.all():
            mapped_type =  DESCRIPTORS_TYPES_MAP[descriptor_item.type]
            field_name = str(descriptor_item.get_field_name())
            label = descriptor_item.name
            fields[field_name] = DyField(name=field_name, label=label,type=mapped_type['model'], model=datamodel, args=mapped_type['args'], kwargs=mapped_type['kwargs'])
            fields[field_name].save()
        return fields
    
    def generate_meta(self):
    
        datamodel = self.dymodel
        fields = {}
        parsers = {}
        geo_fields = []
        non_geo_fields = []
    
        for descriptor_item in self.items.all():
            mapped_type =  DESCRIPTORS_TYPES_MAP[descriptor_item.type]
            field_name = str(descriptor_item.get_field_name())
            label = descriptor_item.name
             
            if utils.is_geom_field(mapped_type['model']):
                geo_fields.append(field_name)
            else:
                non_geo_fields.append(field_name)
                
            fields[field_name] = {"name":field_name, "label":label,"type":descriptor_item.type}
            parsers[field_name] = mapped_type['parser']

        return  {'fields':fields, 'parsers':parsers, 'geo_fields' : geo_fields, 'non_geo_fields' : non_geo_fields}
    
    
    
    #todo: split into simpler methods (generate_dymodel, load_data_from_source) 
    def load_data(self):
        datamodel= self.generate_dymodel()
        fields = self.generate_dymodel_fields()
        meta = self.generate_meta()
        parsers = meta['parsers']
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
                    #print "xxx", f, e, parsers[f]
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