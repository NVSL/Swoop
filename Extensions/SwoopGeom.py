

import Swoop
from Rectangle import Rectangle
from CGAL.CGAL_Kernel import \
    Segment_2,\
    Polygon_2,\
    Point_2,\
    Bbox_2,\
    Iso_rectangle_2,\
    do_intersect
import numpy as np
import Dingo.Component
import math

def np2cgal(numpy_point):
    return Point_2(numpy_point[0], numpy_point[1])

def isinstance_any(object, list):
    for c in list:
        if isinstance(object, c):
            return True
    return False


class GeometryMixin(object):
    def get_point(self, i=None):
        """
        Get a coordinate as a numpy array
        Ex: wire.get_point(1) would be (wire.get_x1(), wire.get_y1())
        """
        if i is not None:
            i = str(i)
            return np.array([getattr(self, "get_x" + i)(), getattr(self, "get_y" + i)()])
        else:
            return np.array([getattr(self, "get_x")(), getattr(self, "get_y")()])

    def set_point(self, i, pt):
        i = str(i)
        getattr(self,"set_x" + i)(pt[0])
        getattr(self,"set_y" + i)(pt[1])

    def _get_cgal_elem(self):
        """
        Get a cgal geometry element representing this object, if any
        Width is only considered for Wire
        """
        if isinstance(self, Swoop.Rectangle):
            verts = list(Rectangle(self.get_point(1), self.get_point(2)).vertices())
            verts.reverse()     # put it in CCW order
            if self.get_rot() is not None:
                angle_obj = Dingo.Component.angle_match(self.get_rot())
                angle = math.radians(angle_obj['angle'])
                if angle_obj['mirrored']:
                    angle *= -1
                origin = (verts[0] + verts[1]) / 2.0    # midpoint
                rmat = Rectangle.rotation_matrix(angle)
                for i,v in enumerate(verts):
                    verts[i] = np.dot(v - origin, rmat) + origin
            return Polygon_2(map(np2cgal, verts))
        elif isinstance(self, Swoop.Wire):
            p1 = self.get_point(1)
            p2 = self.get_point(2)
            if self.get_width() is None:
                return Segment_2(np2cgal(p1), np2cgal(p2))
            else:
                # Wire has width
                # This is important to consider because wires can represent traces
                # When doing a query, it is important we can pick up the trace
                if p1[0] > p2[0]:
                    p1,p2 = p2,p1   # p1 is the left endpoint
                elif p1[0]==p2[0] and p1[1] > p2[1]:
                    p1,p2 = p2,p1   # or the bottom

                vec = (p2 - p1)
                vec /= np.linalg.norm(vec)          # Normalize
                radius = np.array(vec[1], -vec[0])
                radius *= self.get_width()/2.0     # "Radius" of the wire, perpendicular to it

                vertices = []
                # Go around the vertices of the wire in CCW order
                # This should give you a rotated rectangle
                vertices.append(np2cgal( p1 + radius ))
                vertices.append(np2cgal( p2 + radius ))
                vertices.append(np2cgal( p2 - radius ))
                vertices.append(np2cgal( p1 - radius ))
                return Polygon_2(vertices)
        elif isinstance(self, Swoop.Polygon):
            return Polygon_2([np2cgal(v.get_point()) for v in self.vertices()])
        else:
            return None

    def get_bounding_box(self):
        """
        Get the minimum bounding box enclosing this list of primitive elements
        More accurate than self_get_cgal_elem().bbox(), because it accounts for segment width
        """
        def max_min(vertex_list, width=None):
            max = np.maximum.reduce(vertex_list)
            min = np.minimum.reduce(vertex_list)
            if width is not None:
                radius = np.array([width, width]) / 2.0
                max += radius
                min -= radius
            return max,min

        if isinstance(self, Swoop.Polygon):
            vertices = [v.get_point() for v in self.get_vertices()]
            return Rectangle(*max_min(vertices, self.get_width()))
        elif isinstance(self, Swoop.Wire):
            vertices = [self.get_point(1), self.get_point(2)]
            return Rectangle(*max_min(vertices, self.get_width()))
        elif isinstance(self, Swoop.Rectangle):
            #get_cgal_elem already handles rotation
            bbox = self._get_cgal_elem().bbox()
            return Rectangle.from_cgal_bbox(bbox)
        elif isinstance(self, Swoop.Via) or isinstance(self, Swoop.Pad):
            #TODO: pads with funny shapes
            center = self.get_point()
            if self.get_diameter() is None:
                # Gotta figure it out from drill
                radius = (0.351 + 1.251*self.get_drill())/2.0 * np.ones(2)
                return Rectangle(center - radius, center + radius)
            else:
                radius = self.get_diameter()/2.0 * np.ones(2)
                return Rectangle(center - radius, center + radius)
        elif isinstance(self, Swoop.Smd):
            center = self.get_point()
            radius = np.array([self.get_dx(), self.get_dy()]) / 2.0
            if self.get_rot() is not None:
                angle = Dingo.Component.angle_match(self.get_rot())
                radius = abs(Rectangle.rotation_matrix(math.radians(angle['angle'])).dot(radius))
            return Rectangle(center - radius, center + radius)
        else:
            return None


class GeoElem(object):
    """
    A CGAL shape and a Swoop object
    """
    def __init__(self, cgal_elem, swoop_elem):
        self.cgal_elem = cgal_elem
        self.swoop_elem = swoop_elem
        bbox = cgal_elem.bbox()

        #do_intersect only works with iso_rectangle, not bbox
        self.iso_rect = Iso_rectangle_2(bbox.xmin(), bbox.ymin(), bbox.xmax(), bbox.ymax())

    def overlaps(self, iso_rect_query):
        """
        Does this element overlap the bounding box?

        :param bbox_query: CGAL bounding box to check against
        :return: Bool
        """
        if isinstance(self.cgal_elem, Polygon_2):
            #do_intersect does not work with Polygon_2 for some reason
            #Check bounding box intersection first, it's faster
            if do_intersect(self.iso_rect, iso_rect_query):
                for edge in self.cgal_elem.edges():
                    if do_intersect(edge, iso_rect_query):
                        return True
            return False
        else:
            return do_intersect(self.cgal_elem, iso_rect_query)

WithMixin = Swoop.Mixin(GeometryMixin, "geo")

class BoardFile(Swoop.From):
    """
    A wrapper around Swoop.BoardFile that adds some geometric methods
    """
    def __init__(self, filename):
        """
        Completely overrides the parent constructor

        Need a few things to init from:
        -All <elements> (parts on the board)
        -Random other stuff from <signals> or <plain>

        :param filename: .brd file to create self from
        :return:
        """
        # From needs this in order to work
        super(BoardFile, self).__init__(WithMixin.from_file(filename))

        # Tuples of (geometry element, swoop element)
        # Everything that you can see on the board
        self._elements = []

        #Add all the stuff in <signals>
        #First wires
        for wire in self.get_signals().get_wires():
            self._elements.append(GeoElem(wire._get_cgal_elem(), wire))

        #Then vias
        for via in self.get_signals().get_vias():
            #Circular kernel does not have python bindings yet...so just use bounding box
            rect = via.get_bounding_box()
            self._elements.append(GeoElem(Iso_rectangle_2(*rect.bounds_tuple), via))

        # Then plain elements
        for elem in self.get_plain_elements():
            cgal_elem = elem._get_cgal_elem()
            if cgal_elem is not None:
                self._elements.append(GeoElem(cgal_elem, elem) )

        #TODO: actual elements after handling mirroring and translation


    def draw_rect(self, rectangle, layer):
        swoop_rect = WithMixin.class_map["rectangle"]()
        swoop_rect.set_point(1, rectangle.bounds[0])
        swoop_rect.set_point(2, rectangle.bounds[1])
        swoop_rect.set_layer(layer)
        self.add_plain_element(swoop_rect)

    def get_overlapping(self, rectangle_or_xmin, ymin=None, xmax=None, ymax=None):
        if isinstance(rectangle_or_xmin, Rectangle):
            query = Iso_rectangle_2(*rectangle_or_xmin.bounds_tuple)
        else:
            query = Iso_rectangle_2(rectangle_or_xmin, ymin, xmax, ymax)

        return Swoop.From([x.swoop_elem for x in self._elements if x.overlaps(query)])


def from_file(filename):
    return BoardFile(filename)




