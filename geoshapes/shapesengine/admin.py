from django.contrib import admin

from shapesengine.models import CsvSourceDescriptor, SourceDescriptorItem, CsvSource, DyModel

admin.site.register(CsvSourceDescriptor)
admin.site.register(SourceDescriptorItem)
admin.site.register(CsvSource)
admin.site.register(DyModel)