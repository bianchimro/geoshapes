import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.fields.related import ForeignKey    
from django.http import HttpResponse



def instance_dict(instance, key_format=None, recursive=False, related_names=[], properties=[]):
    
    """
    Returns a dictionary containing field names and values for the given instance
    """
    
    if key_format:
        assert '%s' in key_format, 'key_format must contain a %s'
    key = lambda key: key_format and key_format % key or key

    d = {}
    for field in instance._meta.fields:
        attr = field.name
        value = getattr(instance, attr)
        try:
            if value is not None and isinstance(field, ForeignKey):
                if not recursive:
                    value = value._get_pk_val()
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
        
    



