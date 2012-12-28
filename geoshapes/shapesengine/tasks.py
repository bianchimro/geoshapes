from celery import task
from shapesengine.utils import instance_dict

@task()
def add(x, y):
    return x + y

@task()    
def load_dataset_from_source(source, dataset):
    
    source.generate_fields_for_descriptor(descriptor)
    descriptor.load_data()

    return True

@task()    
def load_dataset(descriptor):

    descriptor.load_data()
    descriptor_dict = instance_dict(descriptor, recursive=True, properties=['metadata'])
    return descriptor_dict


