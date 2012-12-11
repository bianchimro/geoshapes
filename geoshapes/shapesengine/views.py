# -*- coding: utf-8 -*-

import json
import os
import datetime
import mimetypes

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.utils.http import urlquote
from django.utils.encoding import smart_str

from django.contrib.auth.decorators import login_required
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.models import User, Group

from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.template import RequestContext, loader, Context

from django.core.servers.basehttp import FileWrapper
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
from django.core.files import File

from django.db.models.loading import get_model

from shapesengine.utils import instance_dict

from shapesengine.models import *





from ajaxuploader.backends.local import LocalUploadBackend
class AjaxUploadBackend(LocalUploadBackend):
    UPLOAD_DIR = 'ajax_upload_worktables'


from ajaxuploader.views import AjaxFileUploader
import_uploader = AjaxFileUploader(AjaxUploadBackend)

    

from ajaxuploader.backends.local import LocalUploadBackend
class AjaxUploadBackend(LocalUploadBackend):
    UPLOAD_DIR = 'ajax_upload_worktables'


from ajaxuploader.views import AjaxFileUploader
import_uploader = AjaxFileUploader(AjaxUploadBackend)

