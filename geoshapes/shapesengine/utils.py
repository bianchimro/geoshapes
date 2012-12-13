
    
from django.db.models.fields.related import ForeignKey    
def instance_dict(instance, key_format=None, recursive=False, related_names=[]):
    
    "Returns a dictionary containing field names and values for the given instance"
    if key_format:
        assert '%s' in key_format, 'key_format must contain a %s'
    key = lambda key: key_format and key_format % key or key

    d = {}
    for field in instance._meta.fields:
        attr = field.name
        value = getattr(instance, attr)
        if value is not None and isinstance(field, ForeignKey):
            if not recursive:
                value = value._get_pk_val()
            else:
                value = instance_dict(value)
        d[key(attr)] = value
    
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
    
    
    return d
    

def field_names_dict(aModel):
    """Returns a dictionary with field verbose names"""
    result = {}
    for field in aModel._meta.fields:
        result[field.name] = field.verbose_name.capitalize()
    return result
