from django.contrib import admin

from shapesengine.models import DatasetDescriptor, DatasetDescriptorItem, CsvSource, DyModel

admin.site.register(DatasetDescriptor)
admin.site.register(DatasetDescriptorItem)
admin.site.register(CsvSource)
admin.site.register(DyModel)