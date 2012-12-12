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

from shapesengine.dynamic_models import get_dataset_model, build_existing_survey_dataset_models

#from shapesengine import signals


DEFAULT_APP_NAME = 'shapesengine'


#TODO: rename SourceDescriptor to DatasetDescriptor
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
        
    
    #TODO: change name and add options    
    def rebuild(self):
        print "a"
        Dataset = self.get_dataset_model(regenerate=True, notify_changes=True)
        print "b"
        
        helpers.delete_db_table(Dataset)
        helpers.create_db_table(Dataset)
        helpers.add_necessary_db_columns(Dataset)
        
        helpers.reregister_in_admin(admin.site, Dataset)
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

    
    
    
#TODO: make concrete class. remove subclasses
class SourceDescriptor(models.Model):
    
    name = models.CharField(max_length=200)
    #todo: not necessary one to one....
    source = models.OneToOneField(Source, related_name='descriptor')
    descriptors = generic.GenericRelation('SourceDescriptorItem', content_type_field='descriptor_type',
                               object_id_field='descriptor_id')
    

    


    def save(self, *args, **kwargs):
    
        if not self.name:
            self.name = self.__class__.__name__ + str(self.source.id) 
    
        
        return super(SourceDescriptor, self).save( *args, **kwargs);
        
        
    
    #todo: split into simpler methods (generate_dymodel, load_data_from_source) 
    def load_data(self):

        try:
            datamodel = DyModel.objects.get(name=self.name)
            datamodel.dyfields.all().delete()

        except:
            datamodel = DyModel(name=self.name)
            datamodel.save()
        
        fields = {}
        parsers = {}
        for descriptor in self.descriptors.all():
            print descriptor.type, descriptor.name
            mapped_type =  DESCRIPTORS_TYPES_MAP[descriptor.type]
            field_name = str(descriptor.get_field_name())
            fields[field_name] = DyField(name=field_name, type=mapped_type['model'], model=datamodel, args=mapped_type['args'], kwargs=mapped_type['kwargs'])
            fields[field_name].save()
            parsers[field_name] = mapped_type['parser']
            
        print 12
        Dataset = datamodel.rebuild()
        print Dataset
        
        
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
            
            instance = Dataset(**kwargs)
            instance.save()
        




#TODO: move to separate module
DESCRIPTORS_TYPES_MAP = {
    'text' : { 'model': 'TextField', 'args' : (), 'kwargs': {'null':True, 'blank':True}, 'parser': str},
    'string' : { 'model': 'CharField', 'args' : (), 'kwargs': { 'max_length' : 200,'null':True, 'blank':True } , 'parser' : str },
    'integer' : { 'model': 'IntegerField', 'args' : (), 'kwargs': {'null':True, 'blank':True }, 'parser': int},
    'float' : { 'model': 'FloatField', 'args' : (), 'kwargs': { 'null':True, 'blank':True }, 'parser': float}
}

DESCRIPTOR_TYPE_CHOICES = []
for x in DESCRIPTORS_TYPES_MAP:
    DESCRIPTOR_TYPE_CHOICES.append([x,x])


class SourceDescriptorItem(models.Model):
    
    #descriptor = models.ForeignKey(SourceDescriptor, related_name = 'items')
    descriptor_type = models.ForeignKey(ContentType)
    descriptor_id = models.PositiveIntegerField()
    descriptor_object = generic.GenericForeignKey('descriptor_type', 'descriptor_id')
    
    order = models.IntegerField(default=0)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=200, choices=DESCRIPTOR_TYPE_CHOICES)

    def get_field_name(self):
        return slugify(self.name).replace("-", "_")



#DyModel.objects.all().delete()
#DyField.objects.all().delete()

#TODO: user method in helpers...
for x in DyModel.objects.all():
    Dataset = x.get_dataset_model(regenerate=True, notify_changes=True)
    #helpers.delete_db_table(Dataset)
    #helpers.create_db_table(Dataset)
    #helpers.add_necessary_db_columns(Dataset)
    helpers.reregister_in_admin(admin.site, Dataset)
    helpers.notify_model_change(Dataset)

#post_save.connect(signals.survey_post_save, sender=Survey)


"""


x = DyModel(name="test")
x.save()

x1 = DyField(name='ex', type='CharField', model=x, kwargs={'max_length': 100})
x1.save()

x.rebuild()
"""