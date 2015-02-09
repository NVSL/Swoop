import csv
import re
import HighEagle

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
    def __init__(self, partObjectType, partTypeName, dbs):
        self.srcFiles = dbs
        self.partTypeName = partTypeName
        self.partType = partObjectType
        self.parts = []
        for f in dbs:
            try:
                print "Loading '" + f + "'...",
                r = csv.DictReader(open(f, "rU"))
                line = 1
                count = 0
                for h in r:
                    line = line + 1
                    #p = partObjectType(_db_rec=h)
                    if h["Stock"].upper() == "": #"STOCK" and h["Stock"].upper() != "SPECIAL-ORDER":
                        continue;
                                                
                    count = count + 1
                    #p = partObjectType(_db_rec=h)
                    try:
                        p = partObjectType(_db_rec=h)
                    except Exception as e:
                        raise Exception("In file '" + f + "' line " + str(line) +  ": " + str(e.args[0]))
                    self.parts.append(p)
                    p.db.value = f
                #print self.name + " = " + "\n".join(map(str,self.parts))
            except KeyError as e:
                raise HighEagle.HighEagleError("Database laod error for '" + f + "' line " + str(line) + ": Missing field " + str(e))
            print str(count) + " parts."
