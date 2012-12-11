from django.db import models
from django.db.models.loading import cache
from django.contrib.auth.models import User

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ValidationError

#from django.db.models.signals import post_save, pre_save, pre_delete, post_delete
    
from picklefield.fields import PickledObjectField
import csv

from shapesengine import utils
from shapesengine import helpers
from model_utils.managers import InheritanceManager

#from shapesengine import signals

import uuid

DEFAULT_APP_NAME = 'shapesengine'
def generate_hash_string():
    return str(uuid.uuid4).replace("-","")

# Create your models here.
class DyModel(models.Model):
    name=models.CharField(max_length=200)
    alive = models.BooleanField(default=True)
    
    def __unicode__(self):
        return u'%s' % self.name
        
    def generate_model(self):
    
        fields = self.dyfields.all()
        
        attrs = {
            '__module__': DEFAULT_APP_NAME + ".models",
            '__unicode__': lambda s: '%s' % self.name,
            '_hash' : generate_hash_string()
        }
        
        for field in fields:
            field_type = getattr(models, field.type)
            attrs[field.name] = field_type(*field.args, **field.kwargs)
        
        klass = type(str(self.name), (models.Model,), attrs)
        return klass
    
        
    def rebuild(self):
       
            
        klass = self.generate_model()
        
        #utils.generate_table(klass)
        #utils.generate_admin(klass)
        
        helpers.delete_db_table(klass)
        helpers.create_db_table(klass)
        
        from django.contrib import admin
        
        
        #utils.generate_admin(klass)
        #admin.site.register(klass)
        helpers.reregister_in_admin(admin.site, klass)
        helpers.notify_model_change(klass)
    
    
    
class DyField(models.Model):

    name=models.CharField(max_length=200)
    type=models.CharField(max_length=200)
    model = models.ForeignKey(DyModel, related_name='dyfields')
    args = PickledObjectField()
    kwargs = PickledObjectField()



class Source(models.Model):
    fields = PickledObjectField()
    objects = InheritanceManager()



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
            data.append(line)
        f.close()
        return data
        
    
    def save(self, *args, **kwargs):
    
        super(CsvSource, self).save(*args, **kwargs)

    
    
    

class SourceDescriptor(models.Model):

    name = models.CharField(max_length=200)
    source = models.OneToOneField(Source, related_name='descriptor')
    descriptors = generic.GenericRelation('SourceDescriptorItem', content_type_field='descriptor_type',
                               object_id_field='descriptor_id')
    

    def save(self, *args, **kwargs):
    
        if not self.name:
            self.name = self.__class__.__name__ + str(self.source.id) 
            print "aaa", self.name
        super(SourceDescriptor, self).save( *args, **kwargs);
        
        
        
    def load_data(self):
        print 1
        try:
            datamodel = DyModel.objects.get(name=self.name)
            datamodel.dyfields.all().delete()

        except:
            datamodel = DyModel(name=self.name)
            datamodel.save()
        
        fields = {}
        for descriptor in self.descriptors.all():
            print descriptor.type, descriptor.name
            mapped_type =  DESCRIPTORS_TYPES_MAP[descriptor.type]
            fields[descriptor.name] = DyField(name= descriptor.name, type=mapped_type['model'], model=datamodel, kwargs=mapped_type['kwargs'])
            fields[descriptor.name].save()
            
        datamodel.rebuild()

        
        actual_source = Source.objects.select_subclasses().get(pk=self.source.id)
        data = actual_source.get_data()
        klass = datamodel.generate_model()
        klass.objects.all().delete()
        
        
        for d in data:
            kwargs = {}
            for f in fields:
                kwargs[f]= d[f]
            
            instance = klass(**kwargs)
            instance.save()
            
        
        
        
        


    class Meta:
        abstract = True
    


DESCRIPTORS_TYPES_MAP = {
    'text' : { 'model': 'TextField', 'args' : (), 'kwargs': {}},
    'string' : { 'model': 'CharField', 'args' : (), 'kwargs': { 'max_length' : 200 }},
    'integer' : { 'model': 'IntegerField', 'args' : (), 'kwargs': { }},
    'float' : { 'model': 'FloatField', 'args' : (), 'kwargs': { }}
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



class CsvSourceDescriptor(SourceDescriptor):
    pass

    



#DyModel.objects.all().delete()
#DyField.objects.all().delete()
from django.contrib import admin
for x in DyModel.objects.all():
    klass = x.generate_model()
    helpers.reregister_in_admin(admin.site, klass)
    helpers.notify_model_change(klass)

#post_save.connect(signals.survey_post_save, sender=Survey)


"""


x = DyModel(name="test")
x.save()

x1 = DyField(name='ex', type='CharField', model=x, kwargs={'max_length': 100})
x1.save()

x.rebuild()
"""