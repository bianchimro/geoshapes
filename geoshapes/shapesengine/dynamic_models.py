# -*- coding: UTF-8 -*-
import logging

#from django.db import models
from django.contrib.gis.db import models
from md5 import new as md5_constructor
from django.core.cache import cache

from shapesengine import helpers
from shapesengine import utils
DEFAULT_APP_NAME = 'shapesengine'

def get_dataset_model(dymodel, regenerate=False, notify_changes=True):
    """ Takes a survey object and returns a model for survey responses. 
        Setting regenerate forces a regeneration, regardless of cached models.
        Setting notify_changes updates the cache with the current hash.
    """
    name = str(dymodel.id)
    _app_label = DEFAULT_APP_NAME
    _model_name = 'Dataset'+name

    # Skip regeneration if we have a valid cached model
    cached_model = helpers.get_cached_model(_app_label, _model_name, regenerate)
    if cached_model is not None:
        return cached_model

    # Collect the dynamic model's class attributes
    attrs = {
        '__module__': __name__, 
        '__unicode__': lambda s: '%s Dataset' % name
    }

    class Meta:
        app_label = DEFAULT_APP_NAME
        verbose_name = 'Dataset %s' % name
    attrs['Meta'] = Meta

    # Add a field for each question
    fields = dymodel.dyfields.all()
    has_geo_field = False
    for field in fields:
        field_name = field.get_field_name()
        attrs[field_name] = field.get_field()
        if field.type in utils.GEOM_FIELDS:
        
           #adding a geomanager
           attrs['objects'] = models.GeoManager()

    # Add a hash representing this model to help quickly identify changes
    attrs['_hash'] = generate_model_hash(dymodel)

    # A convenience function for getting the data in a predictablly ordered tuple
    attrs['data'] = property(lambda s: tuple(getattr(s, q.slug) for q in questions))

    model = type(_model_name, (models.Model,), attrs)

    # You could create the table and columns here if you're paranoid that it
    # hasn't happened yet. 
    #helpers.create_db_table(model)
    # Be wary though, that you won't be able to rename columns unless you
    # prevent the following line from being run.
    #helpers.add_necessary_db_columns(model)

    if notify_changes:
        helpers.notify_model_change(model)

    return model


#TODO: check if a model is alive ... (if using alive attribute)
def build_existing_dataset_models(model):
    """ Builds all existing dynamic models at once. """
    # To avoid circular imports, the model is retrieved from the model cache
    for dymodel in model.objects.all():
        Dataset = get_dataset_model(dymodel)
        # Create the table if necessary, shouldn't be necessary anyway
        helpers.create_db_table(Dataset)
        # While we're at it...
        helpers.add_necessary_db_columns(Dataset)


def generate_model_hash(dymodel):
    """ Take a survey object and generate a suitable hash for the relevant
        aspect of responses model. 
        For our survey model, a list of the question slugs 
    """

    return md5_constructor(dymodel.get_hash_string()).hexdigest()

