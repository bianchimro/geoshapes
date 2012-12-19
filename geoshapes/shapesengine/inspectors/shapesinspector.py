import csv
import copy
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.gis import geos

from helpers import *    
from datatypes import BASE_TYPES, SQLITE_TYPES
from baseinspector import *

TYPES_MAPPIG  = { 'OFTInteger' : 'integer',
                  'OFTString' : 'string',
                  'OFTReal' : 'float'
    }

class ShapesInspector(BaseInspector):

    def __init__(self, filename, types= BASE_TYPES):
    
        self.filename = filename
        self.types = types
        self.names=[]
        self.meta={}
        
        super(ShapesInspector, self).__init__()
            

    def getLayer(self):
        ds = DataSource(self.filename)
        layer = ds[0]
        return layer


    def analyze(self):
        
        tempMeta = []
        layer = self.getLayer()

        geometry_type = layer.geom_type.name
        srs = layer.srs
        fields = layer.fields
        types = layer.field_types
        
        for i, f in enumerate(fields):
            self.names.append(f)
            t = types[i]
            name = t.__name__
            es_type = TYPES_MAPPIG[name]
            tempMetaItem = {'fieldName': f, 'candidates' : copy.copy(self.types), 'stats' : {} }
            tempMeta.append(tempMetaItem)
            

        data = self.readData(layer, self.names)
        for row in data:
            self.checkRow(row, tempMeta)
                
        self.checkOverrides(tempMeta)
        self.meta = self.convertMeta(tempMeta)
        self.meta['geometry'] = {'type': geometry_type }
        
        
    
    
    def get_feature_properties(self, feature):
        out = {}

        for field in feature.fields:
            out[field] = feature.get(field)
        
        return out
    
    
    def fix_geometry_type(self, geom, source_srid):
        """
        Convert polygons to multipolygons so all features are homogenous in the database.
        """
        
        
        geometry = GEOSGeometry(geom.wkt, srid=source_srid)
        
        """
        if(source_srid != 4326):
            spatref_source = SpatialReference(source_srid)
            spatref_target = SpatialReference('WGS84')
            trans = CoordTransform(spatref_source, spatref_target)
            geometry.transform(trans)
        """
        
        if geom.__class__.__name__ == 'Polygon':
            g = geos.MultiPolygon(geometry)
            return g
        else:
            return geometry
    
    
    def readData(self, layer, names):

        data = []
        for i, feature in enumerate(layer):
            properties = self.get_feature_properties(feature)
            #data.append(properties)
            item = []
            for n in names:
                item.append(properties[n])
            data.append(item)
        
        return data
        
    def getDataAsDict(self, layer=None,source_srid_declared='', simplify_tolerance=0):

        data = []

        if layer is None:
            layer = self.getLayer()
        
        try:
            layer.srs.identify_epsg()
            source_srid = layer.srs.srid
        except:
            if source_srid_declared:
                source_srid = int(source_srid_declared)
            else:
                raise
                
        
        for i, feature in enumerate(layer):
            properties = self.get_feature_properties(feature)
            geometry = feature.geom            
            geometry = self.fix_geometry_type(geometry, source_srid)
            properties['geometry'] = geometry.wkt

            data.append(properties)
        
        
        return data
            
            
        

if __name__ == '__main__':
    import sys
    fn = sys.argv[1]
    inspector = ShapesInspector(fn, types=BASE_TYPES)
    inspector.analyze()
    print inspector.meta
    
    data = inspector.getDataAsDict()
    print data
    
        

        
        