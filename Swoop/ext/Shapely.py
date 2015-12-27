import shapely.geometry as shapes
import shapely.affinity as affinity
import shapely
import shapely.ops
import math
import Swoop
import logging as log
import matplotlib
from matplotlib import pyplot as plt
from descartes import PolygonPatch

strict = False;

class ShapelyEagleFilePart():
    def __init__(self):
        pass
    def get_geometry(self):
        if strict:
            raise NotImplemented("Can't get shape for {}".format(self.__class__.__name__()))
        else:
            return shapes.LineString()

    def apply_width(self, shape):
        return shape.buffer(self.get_width()/2, resolution=16)

    def apply_transform(self, shape):
        if shape.is_empty:
            return shape
        r = shape
        r = affinity.rotate(r, self.get_rotation(), origin=(0,0))
        r = affinity.scale(r, xfact=(-1 if self.get_mirrored() else 1), origin=(0,0))
        return r;
        
class Circle(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self):
        circle = shapes.Point(self.get_x(), self.get_y()).buffer(self.get_radius())
        return self.apply_width(circle)
    
class Rectangle(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self):
        assert not self.get_mirrored()  # When I select "mirrored" in Eagle, it just modifies the rotation angle.

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

class Polygon(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self)

    def get_geometry(self):
        polygon = shapes.Polygon([(v.get_x(), v.get_y()) for v in self.get_vertices()])
        return self.apply_width(polygon)

class Element(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def apply_transform(self, shape):
        r = ShapelyEagleFilePart.apply_transform(self, shape)
        return affinity.translate(r, xoff=self.get_x(), yoff=self.get_y())

    def get_geometry(self, layer=None):
        package = Swoop.From(self.find_package())

        if layer is None:
            parts = (package.get_drawing_elements() +
                     package.get_smds() +
                     package.get_pads())

        else:
            if self.get_mirrored():
                layer = self.get_file().get_mirrored_layer(layer)

            if isinstance(layer, str):
                layer_name = layer
                layer = self.get_file().layer_name_to_number(layer)
            else:
                layer_name =self.get_file().layer_number_to_name(layer)

                                
            parts = (package.
                     get_drawing_elements().
                     with_layer(layer_name) + 
                     
                     package.
                     get_smds().
                     with_layer(layer_name))
                                     
            if layer <= 16:
                parts = parts + package.get_pads()

        shape = shapely.ops.unary_union(parts.get_geometry())
                                    
        return self.apply_transform(shape)

class Wire(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self):
        line = shapes.LineString([(self.get_x1(), self.get_y1()), (self.get_x2(), self.get_y2())])
        r = self.apply_width(line)
        return r


class Smd(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self):
        box = shapes.box(self.get_x()-self.get_dx()/2.0,
                         self.get_y()-self.get_dy()/2.0,
                         self.get_x() + self.get_dx()/2.0,
                         self.get_y() + self.get_dy()/2.0)
        return self.apply_transform(box)
        
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
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self):

        # By default, the radius of the circle of copper
        # is drill radius + 25% of the drill diameter.
        # The percentage is a parameter set in the DRC
        # settings of Eagle.  Swoop doesn't
        # know about the DRC settings, so we
        # just us the default.
        radius = (self.get_drill()/2) + 0.25 * self.get_drill()
    
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
            shape = shape.union(affinity.rotate(shape, 45))
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

        return self.apply_transform(shape)
        
class Via(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

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
                print "skipping " + str(p)
                continue;
            if p:
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
    subfig.set_xlim(-25,25)
    subfig.set_ylim(-25,25)
    subfig.set_aspect(1)

    subfig.xaxis.set_ticks(range(int(math.floor(float(bounds[0]))), int(math.ceil(float(bounds[2])))))
    subfig.yaxis.set_ticks(range(int(math.floor(float(bounds[1]))), int(math.ceil(float(bounds[3])))))
    subfig.xaxis.set_ticks(range(-25,25))
    subfig.yaxis.set_ticks(range(-25,25))
    subfig.grid(True)

    add_multipolygon(subfig, geometry, facecolor=color,alpha=1)

    plt.title(title)
    
    fig.savefig(filename, format='pdf')
    fig.clf()
    # import time    
