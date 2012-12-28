import sys

ACTIVE_VISUALIZATIONS = ['TextVisualization', 'TableVisualization']

def get_view_template_for_class(class_name):
    cls = getattr(sys.modules[__name__], class_name)
    fun = getattr(cls, 'get_view_template');
    return fun()

def get_edit_template_for_class(class_name):
    cls = getattr(sys.modules[__name__], class_name)
    fun = getattr(cls, 'get_edit_template');
    return fun()

def preprocess_context_for_class(class_name, context, visualization_instance):
    cls = getattr(sys.modules[__name__], class_name)
    fun = getattr(cls, 'process_context');
    return fun(context, visualization_instance)



class BaseVisualization(object):

    @classmethod
    def process_context(self, context, visualization_instance):
        return context


class TextVisualization(BaseVisualization):

    @classmethod
    def get_view_template(self):
        return "website/visualization/text.html"
        
    @classmethod    
    def get_edit_template(self):
        return "website/visualization/text_edit.html"
        
        
class TableVisualization(BaseVisualization):

    @classmethod
    def get_view_template(self):
        return "website/visualization/table.html"
        
    @classmethod    
    def get_edit_template(self):
        return "website/visualization/table_edit.html"