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
    def __init__(self, partObjectType, partTypeName, db):
        self.name = db
        self.partTypeName = partTypeName
        self.partType = partObjectType
        self.parts = []
        r = csv.DictReader(open(db, "rU"))
        line = 1
        for h in r:
            line = line + 1
            try:
                p = partObjectType(_db_rec=h)
            except Exception as e:
                raise Exception("In file '" + db + "' line " + str(line) +  ": " + str(e.args[0]))
            self.parts.append(p)
        #print self.name + " = " + "\n".join(map(str,self.parts))
        for l in self.parts:
            l.db.value = db

