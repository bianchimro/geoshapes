import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.fields.related import ForeignKey    
from django.http import HttpResponse



GEOM_FIELDS = ['PointField', 'MultiPointField', 'PolygonField', 'MultiPolygonField', 'LineStringField', 'MultiLineStringField',
            'GeometryCollectionField']
            
DATETIME_FIELDS = ['DateTimeField', 'DateField']

NUMERIC_FIELDS = ['IntegerField', 'FloatField']


def is_geom_field(field_type):
    return field_type.upper() in [x.upper() for x in GEOM_FIELDS]
    
def is_datetime_field(field_type):
    return field_type.upper() in [x.upper() for x in DATETIME_FIELDS]
    


def instance_dict(instance, key_format=None, recursive=False, related_names=[], properties=[], recursiveProperties=False, check_json=True, ignore_fields=[]):
    
    """
    Returns a dictionary containing field names and values for the given instance
    """
    
    if key_format:
        assert '%s' in key_format, 'key_format must contain a %s'
    key = lambda key: key_format and key_format % key or key

    d = {}
    for field in instance._meta.fields:
        attr = field.name
        if attr in ignore_fields:
            continue
        value = getattr(instance, attr)
        try:
            if value is not None and isinstance(field, ForeignKey):
                if not recursive:
                    value = value._get_pk_val()
                else:
                    if recursiveProperties:
                        value = instance_dict(value,key_format=key_format, recursive=False, properties=properties)
                    else:
                        value = instance_dict(value)
                        
            json_val = json.dumps(value, cls=DjangoJSONEncoder)
            d[key(attr)] = value
        except Exception,e:
            print e
            pass
    
    for field in instance._meta.many_to_many:
        if not recursive:
            d[key(field.name)] = [obj._get_pk_val() for obj in getattr(instance, field.attname).all()]
        else:
            try:
                d[key(field.name)] = [instance_dict(obj) for obj in getattr(instance, field.attname).all()]
            except:
                pass
                #d[key(field.name)] = [obj._get_pk_val() for obj in getattr(instance, field.attname).all()]
    
    
    for related in related_names:
        manager = getattr(instance, related)
        objects = manager.all()
        objs = []
        for obj in objects: 
            objs.append(instance_dict(obj))
        d[key(related)] = objs 
        
    
    for prop in properties:
        print "prop", prop, instance
        value = getattr(instance, prop, None)
        d[key(prop)] = value 
    
    
    return d
    

def field_names_dict(aModel):
    """Returns a dictionary with field verbose names"""
    result = {}
    for field in aModel._meta.fields:
        result[field.name] = field.verbose_name.capitalize()
    return result



class AjaxResponse(object):

    def __init__(self, status=200):
        self.status = status
        self.error = None
        self.result = None
        
    
    @property
    def content_json(self):
        out = {'status' : self.status, 'error':self.error, 'result':self.result }
        return json.dumps(out, cls=DjangoJSONEncoder)
        
        
    def as_http_response(self):
        return HttpResponse(self.content_json, mimetype="application/json")
        
        

def cast_or_get_none(fun, value):
    try:
        out = fun(value)
    except:
        out = None
    
    return out


def collect_queryset_rows(queryset, offset=None, limit=None):
    out_objs = []    
    
   
    offset = cast_or_get_none(int, offset)
    limit = cast_or_get_none(int, limit)
    
    print("i", limit, offset)
    
    #basic limit and offset    
    if limit and offset:
        for o in queryset[offset:limit]:
            out_objs.append(instance_dict(o, recursive=True))
        
    else:
        if limit:
            for o in queryset[:limit]:
                out_objs.append(instance_dict(o, recursive=True))
        elif offset:
            for o in queryset[offset:]:
                out_objs.append(instance_dict(o, recursive=True))   
        else:
            for o in queryset:
                out_objs.append(instance_dict(o, recursive=True))   
    
    return out_objs
