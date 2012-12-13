#TODO: probably a class-based approach could be better
DESCRIPTORS_TYPES_MAP = {

    'text' : { 'model': 'TextField', 'args' : (), 'kwargs': {'null':True, 'blank':True}, 'parser': str},
    
    'string' : { 'model': 'CharField', 'args' : (), 'kwargs': { 'max_length' : 200,'null':True, 'blank':True } , 'parser' : str },
    
    'integer' : { 'model': 'IntegerField', 'args' : (), 'kwargs': {'null':True, 'blank':True }, 'parser': int},
    
    'float' : { 'model': 'FloatField', 'args' : (), 'kwargs': { 'null':True, 'blank':True }, 'parser': float}
}


