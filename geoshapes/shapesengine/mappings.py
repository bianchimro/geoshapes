#TODO: probably a class-based approach could be better


#todo: this is ugly (copied from inspectors/datatypes.py"
#centralize this stuff
import datetime

BASE_DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"]

def date(value, formats=BASE_DATE_FORMATS):
    for format in formats:
        try:
            out = datetime.datetime.strptime(value, format) 
            return out
        except:
            pass
    raise ValueError("Could not convert date %s" % value)

def date2sql(value):
    if value is not None:
        return datetime.datetime.strftime(value, "%Y-%m-%d")
    return ''
    

DESCRIPTORS_TYPES_MAP = {

    'text' : { 'model': 'TextField', 'args' : (), 'kwargs': {'null':True, 'blank':True}, 'parser': str},
    
    'string' : { 'model': 'CharField', 'args' : (), 'kwargs': { 'max_length' : 200,'null':True, 'blank':True } , 'parser' : str },
    
    'integer' : { 'model': 'IntegerField', 'args' : (), 'kwargs': {'null':True, 'blank':True }, 'parser': int},
    
    'float' : { 'model': 'FloatField', 'args' : (), 'kwargs': { 'null':True, 'blank':True }, 'parser': float},
    
    'date' : { 'model': 'DateField', 'args' : (), 'kwargs': { 'null':True, 'blank':True }, 'parser': date},
}


