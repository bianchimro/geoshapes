import csv
import copy

from helpers import *    
from datatypes import BASE_TYPES, SQLITE_TYPES
from baseinspector import *


class CSVInspector(BaseInspector):

    def __init__(self, filename, types= BASE_TYPES):
    
        self.filename = filename
        self.types = types
        self.names=[]
        self.meta={}
        
        self._dialect = None
        
        super(CSVInspector, self).__init__()
        
        
    @property
    def dialect(self):
        if self._dialect:
            return self._dialect
        self._dialect = self.getDialect()
        return self._dialect
        
    
    def getDialect(self):
        with open(self.filename, 'rb') as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read(2048))
            return dialect
            
    
    def explainDialect(self):
        
        print "delimiter:", self.dialect.delimiter
        print "quotechar:", self.dialect.quotechar
    


    def analyze(self):

        with open(self.filename, 'rb') as csvfile:
            reader = csv.reader(csvfile, self.dialect)
            #assuming header
            firstline = reader.next()
            print "x", firstline
            self.names = [sanitize(x) for x in firstline]
            tempMeta = [{'fieldName': x, 'candidates' : copy.copy(self.types), 'stats' : {} } for x in self.names]
            
            for row in reader:
                self.checkRow(row, tempMeta)
                
            self.checkOverrides(tempMeta)
            self.meta = self.convertMeta(tempMeta)
            
            
    def getData(self):

        data = []
        with open(self.filename, 'rb') as csvfile:
            reader = csv.DictReader(csvfile, dialect=self.dialect)
            for line in reader:
                xline = {}
                item = []
                for fi in line:
                    fix = sanitize(fi)
                    xline[fix]  = line[fi]
                for name in self.names:
                    value = xline[name]
                    item.append(value)

                data.append(item)

        return data



    def getDataAsDict(self):
        data = []
        with open(self.filename, 'rb') as csvfile:
            reader = csv.DictReader(csvfile, dialect=self.dialect)
            for line in reader:
                xline = {}
                for fi in line:
                    fix = sanitize(fi)
                    xline[fix]  = line[fi]
                data.append(xline)

        return data
                
            
            
    
        
        

if __name__ == '__main__':
    import sys
    fn = sys.argv[1]
    inspector = CSVInspector(fn, types=SQLITE_TYPES)
    inspector.analyze()
    if '--analyze' in sys.argv:
        print inspector.meta
    
    if '--create' in sys.argv:
        inspector.createTable(tablename='test1')
    if '--insert' in sys.argv:
        inspector.insert(tablename='test1')
        

        
        