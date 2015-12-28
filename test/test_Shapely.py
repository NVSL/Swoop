import unittest
import Swoop
import Swoop.ext.Shapely
import os
import shapely
import re

def hash_geo(geo):
    """
    Hash a shapley geometry object by converting it to string, rounding all the floats it contains and taking a hash of the resulting string.  
    
    The rounding prevents false failures due to floating point errors.
    """
    def trim(match):
        return str(round(float(match.group(0)), 5))
    v = re.sub("-?\d+(\.\d+)?", trim, str(geo))
    return hash(v)

def dump(test, geo, title, c, color):
    hash = hash_geo(geo)
    print """("{}", {}, "{}"),""".format(test[0], hash, test[2])
    colors = {"RED":"#ff0000",
              "GREEN":"#00ff00",
              "BLACK":"#000000",
              "BLUE":"#0000ff",
              "YELLOW":"#ff00ff",
              "PURPLE":"#ff00ff"
        }
    
    Swoop.ext.Shapely.dump_geometry(geo, "{} ({})".format(title,hash) , "{0:03d}.pdf".format(c), colors[color])


class TestShapely(unittest.TestCase):
    
    def setUp(self):
        self.me = os.path.dirname(os.path.realpath(__file__))
        ShapelySwoop = Swoop.Mixin(Swoop.ext.Shapely, "Shapely")
        self.testbrd1 = ShapelySwoop.from_file(self.me + "/inputs/shapeTest1.brd")
        self.testbrd2 = ShapelySwoop.from_file(self.me + "/inputs/shapeTest2.brd")
        self.testbrd3 = ShapelySwoop.from_file(self.me + "/inputs/shapeTest3.brd")

        self.boardtest = ShapelySwoop.from_file(self.me + "/inputs/test_saving.brd")
        
    def test_element(self):
        tests = [("shapely.ops.cascaded_union(Swoop.From(self.testbrd1).get_elements().get_geometry())", -8745343124844733482, "BLACK"),
                 ("self.testbrd1.get_element('U$1').get_geometry()", 3449774795493592488, "BLACK"),
                 ("self.testbrd1.get_element('U$2').get_geometry()", 2947786369872830885, "BLACK"),
                 ("self.testbrd1.get_element('U$2').get_geometry(layer_query='Top')", -2316119240083132091, "RED"),
                 ("shapely.ops.cascaded_union(Swoop.From(self.testbrd1).get_elements().get_geometry(layer_query='Top'))", -1405743727263307022, "RED"),
                 ("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry())", -5984626191484754127, "BLACK"),
                 ("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry(layer_query='tPlace'))", 4675948399285872422, "BLACK"),
                 ("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry(layer_query='bPlace'))", -8147871516156910189, "BLACK"),
                 ("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_element('U$1').get_geometry(layer_query='Top'))", -5301026454227315084, "RED"),
                 ("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_element('U$1').get_geometry(layer_query='Bottom'))", -5999577188847035307, "BLUE"),
                 ("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry(layer_query='tTest2'))", -8049353574747205132, "PURPLE"),
                 ("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry(layer_query='bTest2'))", 3934649351525441535, "YELLOW"),
                 ("shapely.ops.cascaded_union(self.boardtest.get_geometry())", -138569437861972423, "BLACK"),
             ]

        c = 0
        for i in tests:
            geo = eval(i[0])
            #dump(i, geo, i[0], c, i[2])
            self.assertEqual(hash_geo(geo), i[1], "Geometry failure on test {}".format(c))
            c = c + 1
