#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist

from . import utils

def survey_post_save(sender, instance, created, **kwargs):
    """ Ensure that a table exists for this logger. """

    # Force our response model to regenerate
    klass = instance.generate_model()

    # Create a new table if it's missing
    utils.create_db_table(klass)

    # Reregister the model in the admin
    utils.reregister_in_admin(admin.site, klass)

    # Tell other process to regenerate their models
    utils.notify_model_change(klass)

"""
def survey_pre_delete(sender, instance, **kwargs):
    Response = instance.Response

    # delete the data tables? (!)
    #utils.delete_db_table(Response)

    # unregister from the admin site
    utils.unregister_from_admin(admin.site, Response)
"""