#TODO: probably a class-based approach could be better

#reusing inspector date function
from shapesengine.inspectors.datatypes import date

DESCRIPTORS_TYPES_MAP = {

    'text' : { 'model': 'TextField', 'args' : (), 'kwargs': {'null':True, 'blank':True}, 'parser': str},
    
    'string' : { 'model': 'CharField', 'args' : (), 'kwargs': { 'max_length' : 200,'null':True, 'blank':True } , 'parser' : str },
    
    'integer' : { 'model': 'IntegerField', 'args' : (), 'kwargs': {'null':True, 'blank':True }, 'parser': int},
    
    'float' : { 'model': 'FloatField', 'args' : (), 'kwargs': { 'null':True, 'blank':True }, 'parser': float},
    
    'date' : { 'model': 'DateField', 'args' : (), 'kwargs': { 'null':True, 'blank':True }, 'parser': date},
    
    'Polygon' : { 'model': 'MultiPolygonField', 'args' : (), 'kwargs': { 'null':True, 'blank':True }, 'parser': str},
    
    'LineString' : { 'model': 'LineStringField', 'args' : (), 'kwargs': { 'null':True, 'blank':True }, 'parser': str},
    
    'Point' : { 'model': 'PointField', 'args' : (), 'kwargs': { 'null':True, 'blank':True }, 'parser': str},

#??
#    'Point25D' : { 'model': 'PointField', 'args' : (), 'kwargs': { 'null':True, 'blank':True }, 'parser': str},    


}



FILTERS_TYPES_MAP = {

    'text' : [{'name' : 'contains', 'operator' : 'contains' }, {'name' : 'startswith', 'operator' : 'startswith'}],
    'string' : [{'name' : 'contains', 'operator' : 'contains' }, {'name' : 'startswith', 'operator' : 'startswith'}],
    'integer' : [{'name' : 'greater than', 'operator' : 'gt' }, {'name' : 'less than', 'operator' : 'lt'}],
    'float' : [],
    'date' : []
}