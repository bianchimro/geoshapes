import os
import zipfile
import tempfile
import shutil

from django.contrib.gis import gdal

from django.conf import settings
SHP_UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, "shapes_uploads")

class ShapeChecker(object):

    def get_target_paths(self, zip_path):
        
        file_name = os.path.split(zip_path)[-1]
        name, ext = os.path.splitext(file_name)
        found = False
        
        counter = 0
        while not found:
            target_dir = os.path.join(SHP_UPLOAD_DIR, name)
            exists = os.path.exists(target_dir)
            if exists:
                name = name + "_" + str(counter)
                counter += 1
            else:
                found = True
        
        target_path = os.path.abspath(os.path.join(target_dir, file_name))
        return target_dir, target_path



    def handle(self,zip_path):
        """ Upload the file data, in chunks, to the SHP_UPLOAD_DIR specified in settings.py.
        """
        # ensure the upload directory exists
        if not os.path.exists(SHP_UPLOAD_DIR):
            os.makedirs(SHP_UPLOAD_DIR) 
        
        # contruct the full filepath and filename
        target_path,target_dir = self.get_target_paths(zip_path)
        # write the zip archive to final location
        self.unzip_file(zip_path, target_dir)
        
        files_list  = os.listdir(target_dir)
        shape_candidate = self.get_shape_candidate(files_list)
        return os.path.abspath(os.path.join(target_dir, "%s.shp"% shape_candidate))

    def write_file(self, src, dst):
         shutil.copyfile(src, dst)
         
    
    def unzip_file(self, zip_path, target_dir):
        zfile = zipfile.ZipFile(zip_path)
        zfile.extractall(target_dir)

    def check_zip_contents(self, ext, zip_file):
        if not True in [info.filename.endswith(ext) for info in zip_file.infolist()]:
            return False
        return True
        
    
    def get_shape_candidate(self, files_list):
        shape_candidate = None
        basenames = dict()
        
        for file_name in files_list:
            name = os.path.split(file_name)[-1]
            basename, ext = os.path.splitext(name)
            if basename in basenames:
                basenames[basename]['count'] += 1
            else:
                 basenames[basename] = { 'count' : 1, 'has_shape' : False}
            has_shape = (ext.lower() == '.shp')
            basenames[basename]['has_shape'] = basenames[basename]['has_shape'] or has_shape
            

        for basename in basenames:
            if basenames[basename]['has_shape'] and  basenames[basename]['count'] >= 3:
                shape_candidate =  basename
                break
                
        return shape_candidate
    
        
    def validate(self,zip_path):
        """ Validate the uploaded, zipped shapefile by unpacking to a temporary sandbox.
        """
        # create a temporary file to write the zip archive to
        tmp = tempfile.NamedTemporaryFile(suffix='.zip', mode = 'w')
        # write zip to tmp sandbox
        self.write_file(zip_path, tmp.name)

        if not zipfile.is_zipfile(tmp.name):
            return False, 'That file is not a valid Zip Archive'

        # create zip object
        zfile = zipfile.ZipFile(tmp.name)
        

        # ensure proper file contents by extensions inside
        if not self.check_zip_contents('shp', zfile):
            return False, 'Found Zip Archive but no file with a .shp extension found inside.'
        elif not self.check_zip_contents('prj', zfile):
            return False, 'You must supply a .prj file with the Shapefile to indicate the projection.'
        elif not self.check_zip_contents('dbf', zfile):
            return False, 'You must supply a .dbf file with the Shapefile to supply attribute data.'
        elif not self.check_zip_contents('shx', zfile):
            return False, 'You must supply a .shx file for the Shapefile to have a valid index.'

        # unpack contents into tmp directory
        tmp_dir = tempfile.gettempdir()
        zfile.extractall(tmp_dir)
        files_list = zfile.namelist()
        
        #looking for the shape. whe must have 3 files with the same name
        shape_candidate = self.get_shape_candidate(files_list)
        

        if not shape_candidate:
            return False, "No suitable shapefile found"
            
        ds_name = shape_candidate
        
        # ogr needs the full path to the unpacked 'file.shp'
        full_path = '%s%s%s.shp' % (tmp_dir,os.path.sep,ds_name)
        ds = gdal.DataSource(full_path)
        
        # shapefiles have just one layer, so grab the first...
        layer = ds[0]
        
        # one way of testing a sane shapefile...
        # further tests should be able to be plugged in here...
        if layer.test_capability('RandomRead'):
            if str(ds.driver) == 'ESRI Shapefile':
                return True, None
            else:
                return False, "Sorry, we've experienced a problem on our server. Please try again later."
        else:
            return False, 'Cannot read the shapefile, data is corrupted inside the zip, please try to upload again' 