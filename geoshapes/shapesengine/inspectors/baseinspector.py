import csv
import copy

from helpers import *    
from datatypes import BASE_TYPES, SQLITE_TYPES


class BaseInspector(object):


    def analyze(self):
        raise NotImplementedError()
        
    
    def getData(self):
        raise NotImplementedError()
            

    def getDataAsDict(self):
        raise NotImplementedError()
            
            
    def buildInserts(self, tablename):
        data = self.getData()   
        for row in data:
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

        for i, xx in enumerate(row):
            try:
                x = xx.lstrip().rstrip()
            except:
                x = xx
                
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
        
