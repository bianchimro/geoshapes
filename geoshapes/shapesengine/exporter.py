from django.http import HttpResponse
from django.utils.encoding import smart_str

class BaseExporter(object):
    
    def __init__(self, descriptor, queryset):
        self.descriptor = descriptor
        self.queryset = queryset
    
    def get_content(self):
        raise NotImplementedError()
    
    def get_response(self, filename):
        content = self.get_content()
        self.response = HttpResponse(content, content_type=self.content_type)
        self.response['Content-Disposition'] = 'attachment; filename="%s"' %filename
        #response['Content-Length'] = os.path.getsize(realfilename)
        return self.response   
    
    
    
    
class CSVExporter(BaseExporter):
    content_type = "text/csv"
    #todo: use
    extension = "csv"

    def get_content(self):
        
        content = ''
        
        names = []
        for item in self.descriptor.items.all():
            name = item.get_field_name()
            if name not in self.descriptor.metadata['geo_fields']:
                names.append(name)
        content += ';'.join(names) + "\n"
        
        for obj in self.queryset:
            pieces = []
            for name in names:
                value = getattr(obj, name, None)
                if value is None:
                    value = ''
                pieces.append(smart_str(value).decode('utf-8', 'ignore'))
            content += ';'.join(pieces) + "\n"
                
        return content
    
    
             