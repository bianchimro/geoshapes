import csv
import copy
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.gis import geos

from helpers import *    
from datatypes import BASE_TYPES, SQLITE_TYPES


TYPES_MAPPIG  = { 'OFTInteger' : 'integer',
                  'OFTString' : 'string',
                  'OFTReal' : 'float'
    }

class ShapesInspector(object):

    def __init__(self, filename, types= BASE_TYPES):
    
        self.filename = filename
        self.types = types
        self.names=[]
        self.meta={}
            

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
        
        
        if(source_srid != 4326):
            spatref_source = SpatialReference(source_srid)
            spatref_target = SpatialReference('WGS84')
            trans = CoordTransform(spatref_source, spatref_target)
            geometry.transform(trans)
        
        
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
            #geometry = self.fix_geometry_type(geometry, source_srid)
            properties['geometry'] = geometry.wkt

            data.append(properties)
        
        
        return data
            
            
    def buildInserts(self, tablename):
        with open(self.filename, 'rb') as csvfile:
            reader = csv.reader(csvfile, self.dialect)
            #assuming header
            firstline = reader.next()
            for row in reader:
                values = self.row2python(row)
                insert = "INSERT INTO %s "
                insert += "(" + ','.join(self.names) +")"
                insert += " VALUES("
                pieces = [escapeSQLValue(v) for v in values]
                pi = ','.join(pieces)
                insert += pi
                insert += ");"
                insert = insert % tablename
                
                yield insert
    

    def createTable(self,tablename="TABLE_1"):
        sql = "CREATE TABLE IF NOT EXISTS \""+tablename+"\" (\n"
        if 'id' not in self.names and 'ID' not in self.names:
            sql = sql+"  id INTEGER PRIMARY KEY, \n"
        for field in self.names:
            meta = self.meta[field]
            sql = sql+"  "+field+" \t "+ meta['type'] + ",\n"
        sql = sql[:-2]
        sql += "\n);"
        print sql
        

    def insert(self, tablename="TABLE_1"):
        for statement in self.buildInserts(tablename=tablename):
            print statement
            
    
    def updateStats(self, meta, typeName, x):
        if 'stats_type' not in meta:
            meta['stats_type'] = {}
        if typeName not in meta['stats_type']:
            meta['stats_type'][typeName] = dict()
        
        container = meta['stats_type'][typeName]
            
        if 'min' not in container:
            container['min'] = x
            
        if 'max' not in container:
            container['max'] = x

        if x is not None:
            container['min'] = min(x, container['min'])
            container['max'] = max(x, container['max']) 
    
                
    def checkRow(self, row, tempMeta):
        for i, x in enumerate(row):
            meta = tempMeta[i]
            toRemove = []
            candidates = meta['candidates']
            for typeName in candidates:
                candidate = candidates[typeName]
                typeCheck =  candidate['checker']
                try:
                    value = wrapEmptyValues(typeCheck,x)
                    self.updateStats(meta, typeName, value)
                except ValueError:
                    toRemove.append(typeName)
                except:
                    raise

            for r in toRemove: 
                del candidates[r]
            
            l = len(str(x))    
            if 'maxlenitem' not in meta['stats']:
                meta['stats']['maxlenitem'] = x
                meta['stats']['maxlen'] = l
                
            if l > meta['stats']['maxlen']:
                meta['stats']['maxlen'] = l
                meta['stats']['maxlenitem'] = x
                
                
                
    def row2python(self, row):
        out = []
        for i, name in enumerate(self.names):
            typeName = self.meta[name]['type']
            item = row[i]
            fun = self.types[typeName]['checker']
            converter = self.types[typeName]['converter']
            value = wrapEmptyValues(fun, item)
            value = converter(value)
            out.append(value)
        return out
            
            
        
                    
    def checkOverrides(self, meta):
        for metaItem in meta:
            toRemove = []
            candidates =  metaItem['candidates']
            for typeName in candidates:
                candidate = candidates[typeName]
                if 'overrides' in candidate:
                    toRemove.extend(candidate['overrides'])
                    #recursive removal
                    for ov in candidate['overrides']:
                        if 'overrides' in self.types[ov]:
                            toRemove.extend(self.types[ov]['overrides'])
                        
            toRemove = list(set(toRemove))
            for r in toRemove: 
                try:
                    del candidates[r]
                except:
                    pass
        
    
    def convertMeta(self, tempMeta):
        out = {}
        for metaItem in tempMeta:
            out[metaItem['fieldName']] = dict()
            candidates =  metaItem['candidates']
            out[ metaItem['fieldName']]['types'] = candidates.keys()
            
            out[ metaItem['fieldName']]['type'] = candidates.keys()[0]
            try:
                out[ metaItem['fieldName']]['stats_type'] = metaItem['stats_type'][candidates.keys()[0]]
            except:
                pass
            out[ metaItem['fieldName']]['stats'] = metaItem['stats']
        return out
        
        

if __name__ == '__main__':
    import sys
    fn = sys.argv[1]
    inspector = ShapesInspector(fn, types=BASE_TYPES)
    inspector.analyze()
    print inspector.meta
    
    layer = inspector.getLayer()
    data = inspector.getDataAsDict(layer)
    print data
    
        

        
        