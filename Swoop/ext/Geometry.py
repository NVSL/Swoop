# coding=utf-8

import Swoop
from Swoop.ext.Shapes import Rectangle
import numpy as np
import math
from math import pi
import re

#Make sense out of Eagle's angle attribute and return a hash
def angle_match(angle_str):
    match = re.match("(M?)R(-?\d+)",angle_str)
    if match is None:
        return None
    angle = int(match.group(2))
    return {'angle': angle, 'mirrored': match.group(1)=='M'}

def angle_match_to_str(angle):
    angle_str=""
    if angle['mirrored']:
        angle_str += "M"
    angle_str += "R"
    angle_str += str(angle['angle'])
    return angle_str

def np2cgal(numpy_point):
    from CGAL.CGAL_Kernel import \
        Segment_2,\
        Polygon_2,\
        Point_2,\
        Bbox_2,\
        Iso_rectangle_2,\
        do_intersect
    return Point_2(numpy_point[0], numpy_point[1])

def cgal2np(cgal_point):
    return np.array([cgal_point.x(), cgal_point.y()])

def distance(p1, p2):
    """
    Distnace between 2 numpy points
    :param p1:
    :param p2:
    :return:
    """
    return np.linalg.norm(p1 - p2)


def isinstance_any(object, list):
    for c in list:
        if isinstance(object, c):
            return True
    return False


def angle_normalize(radians):
    return math.fmod(math.fmod(radians,2*pi)+2*pi,2*pi)

def arc_bounding_box(p1, p2, theta):
    """
    Bounding box of the semicircular arc sweeping an angle theta from point p1 to p2
    :param p1: numpy point, start of arc
    :param p2: numpy point, end of arc
    :param theta: angle (in radians), angle swept to the arc
    :return: Rectangle
    """
    assert -2*pi <= theta <= 2*pi, "Invalid radians angle"

    wire_vector = p2 - p1

    # Some magic using the law of sines
    arc_radius = abs(np.linalg.norm(wire_vector) * math.cos(theta/2.0)/math.sin(theta))

    # Rotate the vector p1-c by theta and you get p2-c
    # This code exploits that and solves for c (center)
    # Used Maple code generation
    p1x,p1y = p1[0],p1[1]
    p2x,p2y = p2[0],p2[1]
    center = np.array([
        (p1x - math.cos(theta) * p1x - math.cos(theta) * p2x +
         math.sin(theta) * p1y - p2y * math.sin(theta) + p2x) / (0.2e1 - 0.2e1 * math.cos(theta)),

        (p1y - math.cos(theta) * p1y - math.cos(theta) * p2y -
         math.sin(theta) * p1x + math.sin(theta) * p2x + p2y) / (0.2e1 - 0.2e1 * math.cos(theta))
    ])

    # Convert all rotations to CCW
    # p1 sweeps positive theta to get to p2
    if theta < 0:
        p1,p2 = p2,p1
        theta = abs(theta)

    vertices = [p1, p2]
    v1 = p1 - center
    p1_angle = math.atan2(v1[1],v1[0])     # angle of vector (p1-c)
    for test_angle in [0, pi/2.0, pi, 3*pi/2]:
        # 'rotate' (p1-c) to test angle
        # If rotation was less than theta, this is inside the arc sweep
        if 0 < angle_normalize(test_angle - p1_angle) < theta:
            vertices.append(np.array([center[0] + arc_radius*math.cos(test_angle),
                                      center[1] + arc_radius*math.sin(test_angle)]))
    return Rectangle.from_vertices(vertices)

# Store all information about translation/rotation/mirroring in this class
# Eagle order of operations: rotation, mirroring, translation
class Transform(object):
    def __init__(self, rotation=0, mirrored=False, translation=None):
        self._rotation = rotation
        if translation is None:
            self._translation = np.zeros(2)
        else:
            self._translation = translation
        self._mirrored = mirrored

    def __repr__(self):
        return "Transform({0}, {1}, {2})".format(self.rotation, self.mirrored, self.translation)

    def apply(self, other):
        """
        Apply this transform to some geometric object
        :param other: Any object that supports rotate(angle degrees), mirror(), and move() methods
        :return:
        """
        for m in ["rotate", "mirror", "move"]:
            assert hasattr(other, m), "{0} does not have a {1}() method and cannot be transformed".\
                format(other.__class__,m)
        transformed = other.rotate(self.rotation)
        if self.mirrored:
            transformed = transformed.mirror()
        transformed = transformed.move(self.translation)
        return transformed

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, r):
        self._rotation = r

    @property
    def mirrored(self):
        return self._mirrored

    @property
    def translation(self):
        return self._translation


class GeometryMixin(object):
    def get_mirrored(self):
        """
        Is this object mirrored?
        :return: bool
        """
        return hasattr(self, "get_rot") and \
               self.get_rot() is not None and \
               "M" in self.get_rot()

    def get_point(self, i=0):
        """
        Get a coordinate as a numpy array
        Ex: wire.get_point(1) would be (wire.get_x1(), wire.get_y1())
        """
        if isinstance(self, Swoop.Polygon):
            return self.get_nth_vertex(i).get_point()
        else:
            if hasattr(self, "get_x") and hasattr(self, "get_y"):
                return np.array([getattr(self, "get_x")(), getattr(self, "get_y")()])
            else:
                i = str(i + 1)
                return np.array([getattr(self, "get_x" + i)(), getattr(self, "get_y" + i)()])

    def get_points(self):
        """
        Just get all the points
        """
        for i in range(self.num_points()):
            yield self.get_point(i)

    def get_transform(self):
        """
        Get the transform object that would be required to move this object to where it is from the origin
        """
        if self.num_points() == 1:
            rot = 0
            mirrored = False
            if hasattr(self, "get_rot") and self.get_rot() is not None:
                ang = angle_match(self.get_rot())
                rot = ang['angle']
                mirrored = ang['mirrored']
            return Transform(rotation=rot, translation=self.get_point(), mirrored=mirrored)
        else:
            raise TypeError("{0} has {1} coordinates defined, cannot get a Transform() object".
                            format(self.__class__, self.num_points()))

    def set_point(self, pt, i=0):
        """
        Set a coordinate of this object
        pt is a numpy array
        """
        if isinstance(self, Swoop.Polygon):
            self.get_nth_vertex(i).set_point(pt)
        else:
            if hasattr(self, "get_x") and hasattr(self, "get_y"):
                self.set_x(pt[0])
                self.set_y(pt[1])
            else:
                i = str(i + 1)
                getattr(self,"set_x" + i)(pt[0])
                getattr(self,"set_y" + i)(pt[1])

    def num_points(self):
        """
        Number of points in this object
        E.g., circles have 1, lines have 2 and polygons have arbitrary amounts
        """
        if isinstance(self, Swoop.Polygon):
            return len(self.get_vertices())
        else:
            if hasattr(self, "set_x") and hasattr(self, "set_y"):
                return 1

            i=0
            while hasattr(self, "set_x" + str(i+1)) and hasattr(self, "set_y" + str(i+1)):
                i += 1
            return i


    def _get_cgal_elem(self):
        """
        Get a cgal geometry element representing this object, if any
        Width is only considered for Wire
        """
        from CGAL.CGAL_Kernel import \
            Segment_2,\
            Polygon_2,\
            Point_2,\
            Bbox_2,\
            Iso_rectangle_2,\
            do_intersect

        if isinstance(self, Swoop.Rectangle):
            rect = Rectangle(self.get_point(0), self.get_point(1), check=False)
            verts = list(rect.vertices_ccw())
            if self.get_rot() is not None:
                angle_obj = angle_match(self.get_rot())
                angle = math.radians(angle_obj['angle'])
                if angle_obj['mirrored']:
                    angle *= -1
                origin = rect.center()
                rmat = Rectangle.rotation_matrix(angle)
                for i,v in enumerate(verts):
                    verts[i] = np.dot(v - origin, rmat) + origin
            return Polygon_2(list(map(np2cgal, verts)))

        elif isinstance(self, Swoop.Wire):
            p1 = self.get_point(0)
            p2 = self.get_point(1)
            if self.get_width() is None or self.get_width() == 0:
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
            return Polygon_2([np2cgal(v.get_point()) for v in self.get_vertices()])
        else:
            return None

    def get_bounding_box(self, layer=None, type=None):
        """
        Get the minimum bounding box enclosing this list of primitive elements
        More accurate than self._get_cgal_elem().bbox(), because it accounts for segment width

        :param layer: Swoop layer to filter on
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
            if self.get_curve() is not None:
                theta = math.radians(self.get_curve()) # angle swept by arc
                theta = math.fmod(theta, 2*math.pi)
                p1 = self.get_point(0)  # 2 points on the circle
                p2 = self.get_point(1)
                return arc_bounding_box(p1, p2, theta).pad(self.get_width() / 2.0)
            else:
                vertices = [self.get_point(0), self.get_point(1)]
                return Rectangle(*max_min(vertices, self.get_width()), check=False)
        elif isinstance(self, Swoop.Rectangle):
            #get_cgal_elem already handles rotation
            bbox = self._get_cgal_elem().bbox()
            return Rectangle.from_cgal_bbox(bbox, check=False)
        elif isinstance(self, Swoop.Via) or isinstance(self, Swoop.Pad):
            #These assume default settings
            #Unfortunately, restring can change the sizes of things after import

            center = self.get_point()
            if self.get_diameter() is None:
                # Gotta figure it out from drill
                if self.get_drill() < 1.0:
                    diameter = self.get_drill() + 0.5
                else:
                    diameter = self.get_drill()*1.5
            else:
                diameter = self.get_diameter()
            radius = diameter/2.0 * np.ones(2)

            angle = 0.0
            if isinstance(self, Swoop.Pad) and self.get_rot() is not None:
                angle_m = angle_match(self.get_rot())
                angle = angle_m['angle']
                if angle_m['mirrored']:
                    angle = 180.0 - angle
            rotate_matrix = Rectangle.rotation_matrix(math.radians(angle))

            if self.get_shape() in ['long', 'offset']:
                # This is basically a square pad with 180º arc endcaps
                if self.get_shape()=='offset':
                    center[0] += diameter/2.0   # Center is offset to the left, correct it
                rect = Rectangle(center - radius, center + radius)
                verts = list(rect.vertices())
                verts = [rotate_matrix.dot(v - center) + center for v in verts]
                left_cap = arc_bounding_box(verts[0], verts[3], pi)
                right_cap = arc_bounding_box(verts[2], verts[1], pi)

                rect = Rectangle.union(rect, left_cap)
                rect = Rectangle.union(rect, right_cap)
                return rect
            elif self.get_shape()=='octagon':
                vertex = np.array([diameter/2.0,
                                   diameter/2.0 * math.tan(2*pi / 16 )])
                vertex = rotate_matrix.dot(vertex)
                vertices = []
                rot = Rectangle.rotation_matrix(2*pi/8)
                for i in range(8):
                    vertices.append(vertex.copy() + center)
                    vertex = rot.dot(vertex)
                return Rectangle.from_vertices(vertices, check=True)
            else:
                rect = Rectangle(center - radius, center + radius)
                if self.get_shape()=='square':
                    rect.rotate_resize(angle,origin=center)
                return rect
        elif isinstance(self, Swoop.Smd):
            center = self.get_point()
            radius = np.array([self.get_dx(), self.get_dy()]) / 2.0
            if self.get_rot() is not None:
                angle = angle_match(self.get_rot())
                radius = abs(Rectangle.rotation_matrix(math.radians(angle['angle'])).dot(radius))
            return Rectangle(center - radius, center + radius)
        elif isinstance(self, Swoop.Circle):
            center = self.get_point()
            radius = np.ones(2) * (self.get_radius() + self.get_width()/2.0)
            return Rectangle(center - radius, center + radius)
        elif isinstance(self, Swoop.Hole):
            center = self.get_point()
            radius = np.ones(2) * self.get_drill()/2.0
            return Rectangle(center - radius, center + radius)
        elif isinstance(self, Swoop.Element):
            # Element objects do not have enough information for the bounding box
            # That gets set in the constructor
            if hasattr(self,"_extension_geo_elem"):
                return self._extension_geo_elem.rect
            else:
                tform = self.get_transform()
                bbox = self.find_package().get_bounding_box(layer=layer, type=type)
                if bbox is None:
                    return None
                return tform.apply(bbox)
        elif isinstance(self, Swoop.Package):
            rect = None
            for c in self.get_children():
                if ((layer is None) or (hasattr(c,"get_layer") and c.get_layer()==layer))\
                        and ((type is None) or isinstance(c, type)):
                    r = c.get_bounding_box()
                    if r is not None:
                        if rect is None:
                            rect = r
                        rect = Rectangle.union(rect, r)
            return rect
        else:
            return None


    def move(self, move_vector):
        """
        Offset the position of this by a numpy vector
        """
        for i in range(self.num_points()):
            self.set_point(self.get_point(i) + move_vector, i)

    def rotate(self, degrees):
        """
        Rotate everything around the origin (0,0)
        Positive is counter-clockwise
        """
        rot_mtx = Rectangle.rotation_matrix(math.radians(degrees))
        if isinstance(self, Swoop.Rectangle):
            # Special case: you can't just rotate each vertex :(
            origin = (self.get_point(0) + self.get_point(1)) / 2
            new_origin = rot_mtx.dot(origin)
            self.move(new_origin - origin)
        else:
            for i in range(self.num_points()):
                self.set_point( rot_mtx.dot(self.get_point(i)), i)
        if hasattr(self, "get_rot"):
            rot = self.get_rot() or "R0"
            angle = angle_match(rot)
            angle['angle'] = (angle['angle'] + degrees) % 360
            self.set_rot(angle_match_to_str(angle))

    def mirror(self):
        """
        Flip this object around the Y axis and set any mirrored attributes
        """
        for i in range(self.num_points()):
            v = self.get_point(i)
            v[0] *= -1
            self.set_point(v, i)

        if hasattr(self, "get_rot"):
            rot = self.get_rot() or "R0"
            angle = angle_match(rot)
            angle['mirrored'] = not angle['mirrored']
            self.set_rot(angle_match_to_str(angle))
        if hasattr(self, "get_curve") and self.get_curve() is not None:
            self.set_curve( -self.get_curve() )


class GeoElem(object):
    """
    A CGAL shape and a Swoop object
    """
    def __init__(self, cgal_elem, swoop_elem):
        from CGAL.CGAL_Kernel import \
            Segment_2,\
            Polygon_2,\
            Point_2,\
            Bbox_2,\
            Iso_rectangle_2,\
            do_intersect
        self.cgal_elem = cgal_elem
        self.swoop_elem = swoop_elem
        bbox = cgal_elem.bbox()
        self.rect = Rectangle.from_cgal_bbox(bbox, check=False)

        #do_intersect only works with iso_rectangle, not bbox
        self.iso_rect = Iso_rectangle_2(bbox.xmin(), bbox.ymin(), bbox.xmax(), bbox.ymax())

    def overlaps(self, iso_rect_query):

        """
        Does this element overlap the bounding box?

        :param iso_rect_query: CGAL bounding box to check against
        :return: Bool
        """
        from CGAL.CGAL_Kernel import \
            Segment_2,\
            Polygon_2,\
            Point_2,\
            Bbox_2,\
            Iso_rectangle_2,\
            do_intersect,\
            ON_BOUNDED_SIDE,\
            ON_BOUNDARY
        if isinstance(self.cgal_elem, Polygon_2):
            #do_intersect does not work with Polygon_2 for some reason
            #Check bounding box intersection first, it's faster
            if do_intersect(self.iso_rect, iso_rect_query):
                # Check polygon edges crossing the rectangle
                for edge in self.cgal_elem.edges():
                    if do_intersect(edge, iso_rect_query):
                        return True
                # Check rectangle vertices inside the polygon
                for i in range(4):
                    b = self.cgal_elem.bounded_side(iso_rect_query.vertex(i))
                    if b==ON_BOUNDED_SIDE or b==ON_BOUNDARY:
                        return True
            return False
        else:
            return do_intersect(self.cgal_elem, iso_rect_query)

# Primitive drawing elements: Pad, Smd, Via, Rectangle, Wire, Polygon, Text?

# And now some monkey patching

def get_package_moved(self):
    return self.package_moved
Swoop.Element.get_package_moved = get_package_moved

WithMixin = Swoop.Mixin(GeometryMixin, "geo")

class BoardFile(Swoop.From):
    """
    A wrapper around Swoop.BoardFile that adds some geometric methods

    Requires CGAL
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
        from CGAL.CGAL_Kernel import \
            Segment_2,\
            Polygon_2,\
            Point_2,\
            Bbox_2,\
            Iso_rectangle_2,\
            do_intersect

        # From needs this in order to work
        # Call from_file in Swoop and get a Swoop.BoardFile
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


        #Stuff in <plain>
        for elem in self.get_plain_elements():
            cgal_elem = elem._get_cgal_elem()
            if cgal_elem is not None:
                self._elements.append(GeoElem(cgal_elem, elem) )

        # The actual elements in <elements>
        # Each element will be represented as a rotated rectangle
        # The element's children, after translation and rotating, will be in the package_moved attribute
        for elem in self.get_elements():
            package = self.get_libraries().get_package(elem.get_package())
            rect = package.get_children().get_bounding_box().reduce(Rectangle.union)

            if elem.get_rot() is not None:
                angle = angle_match(elem.get_rot())
            else:
                angle = {'angle': 0, 'mirrored': False}
            rotmatx = Rectangle.rotation_matrix(math.radians(angle['angle']))
            origin = elem.get_point()
            # Convert rotated rectangle to polygon
            poly = []
            for v in rect.vertices_ccw():
                vr = rotmatx.dot(v)         # rotate before mirroring
                if angle['mirrored']:
                    vr[0] *= -1
                poly.append(np2cgal(vr + origin))

            # Create a copy of the package with all the children rotated/moved
            elem.package_moved = package[0].clone()
            for package_elem in elem.package_moved.get_children():
                package_elem.rotate(angle['angle'])
                if angle['mirrored']:
                    package_elem.mirror()
                package_elem.move(origin)

            geom = GeoElem(Polygon_2(poly), elem)
            self._elements.append(geom)
            elem._extension_geo_elem = geom

        #Finally, the board outline
        outline = self.get_plain_elements().\
            filtered_by(lambda e: hasattr(e, "get_layer")).\
            with_layer("Dimension")

        if len(outline) > 0:
            self.bbox = outline.get_bounding_box().reduce(Rectangle.union)

    def draw_rect(self, rectangle, layer):
        swoop_rect = WithMixin.class_map["rectangle"]()
        swoop_rect.set_point(rectangle.bounds[0], 0)
        swoop_rect.set_point(rectangle.bounds[1], 1)
        swoop_rect.set_layer(layer)
        self.add_plain_element(swoop_rect)

    def draw_circle(self, center, radius, layer, width=None):
        """
        Draw a circle. Width of None means it's a filled in circle
        :param center: center (numpy point)
        :param radius:
        :param layer: Swoop layer
        :param width:
        :return:
        """
        swoop_circ = WithMixin.class_map["circle"]()
        swoop_circ.set_point(center)
        swoop_circ.set_layer(layer)
        if width is None:
            #Circle is filled in
            swoop_circ.set_width(radius)
            swoop_circ.set_radius(radius/2.0)
        else:
            swoop_circ.set_width(width)
            swoop_circ.set_radius(radius)
        self.add_plain_element(swoop_circ)

    def draw_text(self, origin, text):
        text = WithMixin.class_map["text"]()

    def get_overlapping(self, rectangle_or_xmin, ymin=None, xmax=None, ymax=None):
        from CGAL.CGAL_Kernel import \
            Segment_2,\
            Polygon_2,\
            Point_2,\
            Bbox_2,\
            Iso_rectangle_2,\
            do_intersect
        if isinstance(rectangle_or_xmin, Rectangle):
            query = Iso_rectangle_2(*rectangle_or_xmin.bounds_tuple)
        else:
            query = Iso_rectangle_2(rectangle_or_xmin, ymin, xmax, ymax)

        return Swoop.From([x.swoop_elem for x in self._elements if x.overlaps(query)])

    def get_bounding_box(self):
        return self.bbox

    def get_element_shape(self, elem_name):
        """
        Get the internal CGAL element associated with this element
        (These are only valid for things in the <elements> section)

        :param elem_name: Name of element on board
        :return: CGAL shape
        """
        for elem in self._elements:
            if isinstance(elem.swoop_elem, Swoop.Element)\
                    and elem.swoop_elem.get_name()==elem_name:
                return elem.cgal_elem


def from_file(filename):
    if filename.endswith(".brd"):
        return BoardFile(filename)
    else:
        return Swoop.From(WithMixin.from_file(filename))

