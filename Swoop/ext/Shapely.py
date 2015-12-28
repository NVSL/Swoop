import shapely.geometry as shapes
import shapely.affinity as affinity
import shapely
import shapely.ops
import math
import Swoop
import logging as log

dumping_geometry_works = True
try:
    import matplotlib
    from matplotlib import pyplot as plt
    from descartes import PolygonPatch
except RuntimeError as e:
    log.error("Can't use matplotlib on macosx due to virtualenv.  Dumping to pdf won't work.  Talk to Steve if you need to fix.")
    dumping_geometry_works = False
              

strict = False;

class ShapelyEagleFilePart():
    def __init__(self):
        pass
    def get_geometry(self, layer_query=None):
        if strict:
            raise NotImplemented("Can't get shape for {}".format(self.__class__.__name__()))
        else:
            return shapes.LineString()

    def apply_width(self, shape):
        if self.get_width() > 0:
            return shape.buffer(self.get_width()/2, resolution=16)
        else:
            return shape

    def apply_transform(self, shape, origin=(0,0)):
        if shape.is_empty:
            return shape
        r = shape
        r = affinity.rotate(r, self.get_rotation(), origin=origin)
        r = affinity.scale(r, xfact=(-1 if self.get_mirrored() else 1), origin=(0,0))
        return r;

    def layer_matches(self, query, layer_name):
        if query is None:
            return True
        
        if isinstance(query, str):
            return query == layer_name
        elif  isinstance(query, int):
            return query == self.get_file().layer_number_to_name(layer)
        elif  isinstance(query, Swoop.Layer):
            return query == query.get_name()
        else:
            raise Swoop.SwoopError("illegal layer query: {}".format(query))
        

class BoardFile(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None):
        brd = Swoop.From(self)

        parts = (brd.get_elements() +
                 brd.get_plain_elements() +
                 brd.get_signals().get_wires() +
                 brd.get_signals().get_vias())

        return shapely.ops.unary_union(parts.get_geometry(layer_query=layer_query))

        
class Circle(ShapelyEagleFilePart):
    # Fixme:  Cut out center
    
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None):
        if self.layer_matches(layer_query, self.get_layer()):
            circle = shapes.Point(self.get_x(), self.get_y()).buffer(self.get_radius())
            return self.apply_width(circle)
        else:
            return shapes.LineString()
    
class Rectangle(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None):
        assert not self.get_mirrored()  # When I select "mirrored" in Eagle, it just modifies the rotation angle.

        if self.layer_matches(layer_query, self.get_layer()):

            # if self.get_mirrored():
            #     mirror = shapely.affinity.scale(xfact=-1, center=(0,0,0))
            # else:
            #     mirror = shapely.affinity.scale(xfact=1, center=(0,0,0))

            box = shapes.box(min(self.get_x1(), self.get_x2()),
                             min(self.get_y1(), self.get_y2()),
                             max(self.get_x1(), self.get_x2()),
                             max(self.get_y1(), self.get_y2()))
            box = affinity.rotate(box, self.get_rotation())

            return box;
        else:
            return shapes.LineString()

class Polygon(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self)

    def get_geometry(self, layer_query=None):
        if self.layer_matches(layer_query, self.get_layer()):
            polygon = shapes.Polygon([(v.get_x(), v.get_y()) for v in self.get_vertices()])
            return self.apply_width(polygon)
        else:
            return shapes.LineString()
            

class Package(ShapelyEagleFilePart):
    
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None):
        package = Swoop.From(self)

        parts = (package.get_drawing_elements() + 
                 package.get_smds() +
                 package.get_pads())

        return shapely.ops.unary_union(parts.get_geometry(layer_query=layer_query))

        
class Element(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def apply_transform(self, shape):
        r = ShapelyEagleFilePart.apply_transform(self, shape)
        return affinity.translate(r, xoff=self.get_x(), yoff=self.get_y())

    def get_geometry(self, layer_query=None):
        if self.get_mirrored() and layer_query is not None:
            layer_query = self.get_file().get_mirrored_layer(layer_query)

        shape = self.find_package().get_geometry(layer_query=layer_query);
        return self.apply_transform(shape)

class Wire(ShapelyEagleFilePart):
    # Fixme: handle curves
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None):
        if self.layer_matches(layer_query, self.get_layer()):
            line = shapes.LineString([(self.get_x1(), self.get_y1()), (self.get_x2(), self.get_y2())])
            r = self.apply_width(line)
            return r
        else:
            return shapes.LineString()
    


class Smd(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None):
        if self.layer_matches(layer_query, self.get_layer()):
            box = shapes.box(self.get_x()-self.get_dx()/2.0,
                             self.get_y()-self.get_dy()/2.0,
                             self.get_x() + self.get_dx()/2.0,
                             self.get_y() + self.get_dy()/2.0)
            return self.apply_transform(box, origin=(self.get_x(), self.get_y()))
        else:
            return shapes.LineString()
        
        
class Module(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);
        
class ModuleInst(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

class Gate(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

class Dimension(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

class Text(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);
                                
class Frame(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

class Hole(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

class Pad(ShapelyEagleFilePart):
    # Fixme: handle other shapes.
    
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def render_pad(self, layer_query, drill, rest_ring):

        # Fixme: Pads should be different sizes or different layers.
        # Fixme: Pads should maybe generate keepout geometry as well?
        
        if layer_query is not None and self.get_file().get_layer(layer_query).get_number() > 16:
            return shapes.LineString()
        

        radius = (drill/2) + rest_ring * drill
    
        if self.get_shape() == "square":
            shape = shapes.box(self.get_x() - radius,
                               self.get_y() - radius,
                               self.get_x() + radius,
                               self.get_y() + radius)
        elif self.get_shape() == "round" or self.get_shape() is None:
            shape = shapes.point.Point(self.get_x(), self.get_y()).buffer(radius)
        elif self.get_shape() == "octagon":
            shape = shapes.box(self.get_x() - radius,
                               self.get_y() - radius,
                               self.get_x() + radius,
                               self.get_y() + radius)
            shape = shape.intersection(affinity.rotate(shape, 45))
        elif self.get_shape() == "long":
            shape = None
        elif self.get_shape() == "offset":
            shape = None
        else:
            raise Swoop.SwoopError("Unknown pad shape: '{}'".format(self.get_shape()))

        if strict and shape is None:
            raise NotImplemented("Geometry for pad shape '{}' is not implemented yet.".format(self.get_shape()))
        elif shape is None:
            shape = shapes.LineString()

        return shape

    def get_geometry(self, layer_query=None):

        shape = self.render_pad(layer_query, self.get_drill(), 0.25)
        # By default, the radius of the circle of copper
        # is drill radius + 25% of the drill diameter.
        # The percentage is a parameter set in the DRC
        # settings of Eagle.  Swoop doesn't
        # know about the DRC settings, so we
        # just us the default.
        return self.apply_transform(shape, origin=(self.get_x(), self.get_y()))
                               
class Via(Pad):
    def __init__(self):
        Pad.__init__(self);

    def get_geometry(self, layer_query=None):
        # This isn't quite right.  Via size is set in the DRC file.
        return self.render_pad(layer_query, self.get_drill(), 0.25)

class Pin(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

class Label(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

class Junction(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);


def dump_geometry(geometry, title, filename, color="#888888"):
    if not dumping_geometry_works:
        log.warn("Can't dump geometry because matplotlib doesn't work in virtualenv.")
        return
    
    fig = plt.figure(2, figsize=(10,10), dpi=90)
    def add_multipolygon(fig, mp, width=0, alpha=1, facecolor='none', edgecolor="#0000ff"):
        if not mp:
            return
        if isinstance(mp, shapely.geometry.polygon.Polygon):
            l = [mp]
        else:
            l = mp.geoms
        for p in l:
            if not isinstance(p, shapely.geometry.polygon.Polygon):
                fig.plot([i[0] for i in p.coords], [i[1] for i in p.coords], color=facecolor)
            elif p:
                ring_patch = PolygonPatch(p, facecolor=facecolor, edgecolor=edgecolor, linewidth=width, alpha=alpha)
                fig.add_patch(ring_patch)

    subfig = fig.add_subplot(111)
    bounds = geometry.bounds
    width  = abs(bounds[2] - bounds[0])
    height = abs(bounds[3] - bounds[1])
    xrange = [bounds[0] - 0.1*width,  bounds[2] + 0.1*width]
    yrange = [bounds[1] - 0.1*height, bounds[3] + 0.1*height]
    subfig.set_xlim(*xrange)
    subfig.set_ylim(*yrange)
    #subfig.set_xlim(-25,25)
    #subfig.set_ylim(-25,25)
    subfig.set_aspect(1)

    subfig.xaxis.set_ticks(range(int(math.floor(float(bounds[0]))), int(math.ceil(float(bounds[2])))))
    subfig.yaxis.set_ticks(range(int(math.floor(float(bounds[1]))), int(math.ceil(float(bounds[3])))))
    subfig.grid(True)

    add_multipolygon(subfig, geometry, facecolor=color,alpha=1)

    plt.title(title)
    
    fig.savefig(filename, format='pdf')
    fig.clf()
    # import time    
