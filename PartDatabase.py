import csv
import re

class Parameter:
    name = None
    type = "str"
    value = None
    key = None
    def __init__(self, name, key, type = "str", parse = lambda x:x, value = None):
        self.name = name
        self.type = type
        self.value = value
        self.key = key
        self.parse = parse
    def __str__(self):
        return self.name + " = " + (str(self.value) if self.value != None else "*")

class PartDB:
    def __init__(self, partObjectType, partType, db):
        self.name = db
        self.partType = partType
        r = csv.DictReader(open(db, "rU"))
        self.parts = [partObjectType(_db_rec=h) for h in r]
        #print self.name + " = " + "\n".join(map(str,self.parts))
        for l in self.parts:
            l.db.value = db

