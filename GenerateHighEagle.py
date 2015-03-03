#!/usr/bin/env python

""".. module:: GenerateHighEagle

.. moduleauthor:: Steven Swanson (swanson@cs.ucsd.edu)

GenerateHighEagle.py generates the file HighEagle.py, which contains a set
of python classes for manipulating eagle files.  The process relies on two
bodies of information.

1.  The contents of this file.  It specifies the characteristic of each class
    that corresponds to a part of an eagle file.  The file defines several
    classes (:class:`Attr`, :class:`List`, :class:`Map`, :class:`Singleton`,
    and :class:`TagClass`) that specify how the Eagle classes should behave.

    This file describes a collections of classes that represent a "flattened"
    version of the XML format described in the Eagle DTD.

2.  The contents of HighEagle.jinja.py.  This contains the template code for
    the classes, a base class for all the classes, and a class to represent
    eagle files, EagleFile.

The classes that this code generates each represent a part of an eagle file
(class :class:`EagleFilePart`).  Instances of this class form a tree.  The root of the
tree is an instance of :class:`SchematicFile`, :class:`BoardFile`, or :class:`LibraryFile`, all of which
are subclasses of :class:`EagleFile`.

Each :class:`EagleFilePart` contains one or more attributes and one or more
'collections' (i.e., lists, maps, or singletons) of :class:`EagleFilePart`s.  For
instance, :class:`SchematicFile` contains a collection that maps library names to
:class:`Library` objects, a list of :class:`Sheet` objects, and a singleton :class:`Description`
instance.

This file defines the set of collections that each subclass of :class:`EagleFilePart`
contains.  Each of these subclasses is represented by a :class:`TagClass` object, which
contains a list (called :code:`sections`) of collections (represented by subclasses
of :class:`Collection` -- namely :class:`Map`, :class:`List`, and :class:`Singleton`).  :class:`TagClass` also
includes a list of attributes (represented by :class:`Attr`).

Each :class:`Attr`, :class:`Map`, :class:`List`, and :class:`Singleton` object includes information necessary to
generate code for it.  This includes mostly pedantic stuff like converting
"-" to "_" in attribute names so they are valid python identifiers, dealing
with eagle tag and attribute names that clash with python reserve words, and
information about which attributes and tags are required and which are
optional.  There's also some support for parsing values (e.g., converting
"yes" to True).

The organization of the :class:`EagleFilePart` hierarchy is similar to the structure
of the eagle XML file.  However, we make it easier to navigate by flattening
it.  For instance, in the eagle file layer defintions live in
:code:`eagle/drawing/layers` and sheets live in :code:`eagle/drawing/schematic/sheets`.  Our
library "flattens" this hierarchy so that :class:`SchematicFile` has a map of
layers and a list of sheets.

To realize this flattened structure, we specify the contents of each
collection using an xpath expression.  All the elements that match the
expression for :class:`Map`, :class:`List`, or :class:`Singleton` will end up in that collection.  The
xpath expressions get passed the constructors for the :class:`Map`, :class:`List`, and :class:`Singleton`.

The final stage is to generate the code.  We use the jinja templating system
for this.  HighEagle.jinja.py contains templates for the :class:`EagleFilePart` subclasses.
It generates code for the constructor, the :code:`from_et()` method to convert for
element tree to :class:`EagleFileParts`, the :code:`get_et()` method for the reverse
conversion, a :code:`clone()` function for copying :class:`EagleFileParts`, and accessors for
attributes (:code:`get_*()` and :code:`set_*()`) and collections (:code:`get_*()` and :code:`add_*()`).

The jinja file also generates a python map called :code:`classMap`.  This map defines
the mapping between tag names and EagleFilePart subclasses, and the :code:`from_et()`
methods use this map to determine what kind of object to instantiate for a
given tag.  My manipulating this map, you can extend classes the parser
generates.  For instance, if you created the class :class:`CoolPart`(Part) (a subclass
of :class:`Part` which represents a <part> tag in an eagle file), set classMap["part"]
= :class:`CoolPart`, and then parse an :class:`EagleFile`, it will be populated with :class:`CoolPart`
objects instead of :class:`Part` objects.  In this way, you can easily extend the
library which additional functionality.

"""

import jinja2 as J2
import argparse
import logging as log
import copy


class Attr:
    """
    Class representing an attribute.
    
    """
    def __init__(self, name, required=False, parse=None, unparse=None,type=None,accessorName=None,xmlName=None):
        """Create a class describing an attribute.

        :param name: The attribute's name.  This is the name used for the member of the :class:`EagleFilePart` object.  For example :code:`foo.netclass` (since :code:`class` clashes with a the Python :code:`class` reserved word.
        :param require: Is the attribute required?
        :param parse: String used to parse to attribute value.  It will be invoked as :code:`parse(x)` where :code:`x` is the contents of the XML attribute.
        :param unparse: String used to unparse the attribute value while generating XML. It will be invoked as :code:`unparse(x)` where :code:`x` is :mod:`HighEagle`'s value for the attribute.  :code:'unparse(parse(x))` should be the identity function.
        :param accessorName:This is the string that will appear in HighEagle API calls.  For example :code:`foo.get_class()`
        :param xmlName:This is string used in the XML representation.  For example, :code:`class`.
        """
        self.name = name.replace("-", "_")
        if xmlName is None:
            self.xmlName = name
        else:
            self.xmlName = xmlName

            #assert self.xmlName is not None
#        print "Is " + str(self.name) + " == " + str(self.xmlName) +"?"
        
        self.type=type
        if accessorName is None:
            self.accessorName = name
        else:
            self.accessorName = accessorName
        self.required = required

        if parse is None:
            self.parse = ""
        else:
            self.parse = parse

        if parse is None:
            self.unparse = ""
        else:
            self.unparse = unparse


class Collection:
    """
    Base class for collections.
    """
    def __init__(self, name, xpath, accessorName=None, suppressAccessors=False, requireTag=False):
        """Create a class describing an attribute.

        :param name: The collection's name.  This will be used as the name of the member in the the :code:`EagleFilePart`.
        :param xpath: XPath expression that matches all the tags that should be held in this collection.
        :param suppressAccessors:  If :code:`True`, don't generate accessor functions.
        :param requireTag: This the tag for this collection must appear in the output XML.  The tag that is inserted are the all-but-last tags of xpath expression. For example if :code:`xpath` is :code:`./foo/bar/baz`, the this will ensure that :code:`./foo/bar` exists.
        :param accessorName:This is the string that will appear in HighEagle API calls.  For example :code:`foo.get_class()`.  By default, this is the last tag in the xpath.  For example if :code:`xpath` is :code:`foo/bar', the :code:`accessorName` will be :code:`bar`.
        :param xmlName: This is string used in the XML representation.  For example, :code:`class`.

        """
        self.name = name
        self.xpath = xpath

        if accessorName is None:
            self.accessorName = xpath.split("/")[-1]
        else:
            self.accessorName = accessorName

        self.suppressAccessors = suppressAccessors
        self.requireTag = requireTag

class Map(Collection):
    """
    Collection that maps strings to items
    """
    def __init__(self, name, xpath, accessorName=None, suppressAccessors=False, requireTag=False, mapkey=None):
        """Create a Map object.
        
        See the documentation for :class:`Collection` for the parameters.  There is one additional parameter:
        
        :param mapkey:  This is the attribute of the contained elements that will be used as the index in the map.

        """
        Collection.__init__(self,name, xpath, accessorName,  suppressAccessors, requireTag)
        self.type = "Map"
        if mapkey is None:
            self.mapkey = "name"
        else:
            self.mapkey = mapkey


class List(Collection):
    """
    Collection that is an ordered list
    """
    def __init__(self, name, xpath, accessorName=None, suppressAccessors=False, requireTag=False):
        """Create a List object.
        
        See the documentation for :class:`Collection` for the parameters. 
        """
        Collection.__init__(self,name, xpath, accessorName,suppressAccessors, requireTag)
        self.type = "List"

class Singleton(Collection):
    """
    Collection with a single element
    """
    def __init__(self, name, xpath, accessorName=None,  suppressAccessors=False, requireTag=False):
        """Create a Singleton object.
        
        See the documentation for :class:`Collection` for the parameters. 
        """
        Collection.__init__(self,name, xpath, accessorName,  suppressAccessors, requireTag)
        self.type = "Singleton"

class TagClass:
    """
    Everything we need to know about an object that can hold the contents of a tag in order ot generate the classes for accessing it.
    """
    def __init__(self,
                 tag,
                 baseclass=None, 
                 classname=None,
                 customchild=False,
                 preserveTextAs=None,
                 attrs=None,
                 sections=None
    ):
        if sections is None:
            self.sections = []
        else:
            self.sections = sections

        self.tag = tag
        self.attrs = attrs
        self.lists = []
        self.maps = []
        self.baseclass = baseclass
        if classname is None:
            self.classname = self.get_tag_initial_cap()
        else:
            self.classname = classname
            
        self.customchild = customchild
        self.maps = [m for m in self.sections if isinstance(m, Map)]
        self.lists = [l for l in self.sections if isinstance(l, List)]
        self.singletons = [s for s in self.sections if isinstance(s, Singleton)]

        if preserveTextAs is None:
            self.preserveTextAs = ""
        else:
            self.preserveTextAs = preserveTextAs
            
    def get_attr_names(self):
        return [x for x in self.attrs]
    def get_list_names(self):
        return [x.name for x in self.lists]
    def get_map_names(self):
        return [x.name for x in self.maps]
    def get_tag_initial_cap(self):
        t = self.tag
        t = t[0].upper() + t[1:]
        return t


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a set of classes for manipulating eagle files")
    parser.add_argument("--out", required=True,  type=str, nargs=1, dest='outfile', help="python output")
    args = parser.parse_args()

    log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
    log.info("Verbose output.")

    tags = {}

    layerAttr = Attr("layer",
                     type="LayerAttr",
                     required=True)

    dxAttr = Attr("dx",
                  type="float",
                  required=True)

    dyAttr = Attr("dy",
                  type="float",
                  required=True)

    xAttr = Attr("x",
                 type="float",
                 required=True)

    yAttr = Attr("y",
                 type="float",
                 required=True)

    rotAttr = Attr("rot",
                   type="str",
                   required=False)

    nameAttr = Attr("name",
                    type="str",
                    required=True)
    
    tags["note"] = TagClass("note",
                            baseclass = "EagleFilePart",
                            preserveTextAs = "text",
                            attrs=[Attr("minversion", required=True),
                                   Attr("version", required=True),
                                   Attr("severity", required=True)])

    tags["library"] = TagClass("library",
                               baseclass = "EagleFilePart",
                               attrs=[Attr("name", required=False)],
                               sections=[Singleton("description", "./description", requireTag=True),
                                         Map("packages", "./packages/package", requireTag=True),
                                         Map("symbols", "./symbols/symbol" , requireTag=True),
                                         Map("devicesets", "./devicesets/deviceset", requireTag=True)])

    tags["schematic"] = TagClass("schematic",
                                 baseclass = "EagleFilePart",
                                 attrs=[Attr("xreflabel", required=False),
                                        Attr("xrefpart", required=False)])

    tags["module"] = TagClass("module",
                              baseclass = "EagleFilePart",
                              attrs=[nameAttr,
                                     Attr("prefix", required=False),
                                     dxAttr,
                                     dyAttr],
                              sections=[Singleton("description", "./description", requireTag=True),
                                        Map("ports", "./ports/port"),
                                        Map("variantdefs", "./variantdefs/variantdef", requireTag=True),
                                        Map("parts", "./parts/part", requireTag=True),
                                        List("sheets", "./sheets/sheet")])

    tags["package"] = TagClass("package",
                               baseclass = "EagleFilePart",
                               attrs=[nameAttr],
                               sections=[Singleton("description", "./description", requireTag=True),
                                         List("drawing_elements","./polygon|./wire|./text|./dimension|./circle|./rectangle|./frame|./hole"),
                                         Map("pads", "./pad"),
                                         Map("smds", "./smd")])

    tags["symbol"] = TagClass("symbol",
                              baseclass = "EagleFilePart",
                              attrs=[nameAttr],
                              sections=[Singleton("description", "./description", requireTag=True),
                                        List("drawing_elements","./polygon|./wire|./text|./dimension|./circle|./rectangle|./frame|./hole"),
                                        Map("pins", "./pin")])

    tags["deviceset"] = TagClass("deviceset",
                                 baseclass = "EagleFilePart",
                                 attrs=[nameAttr,
                                        Attr("prefix", required=False),
                                        Attr("uservalue", required=False)],
                                 sections=[Singleton("description", "./description", requireTag=True),
                                           Map("gates", "./gates/gate", requireTag=True),
                                           Map("devices", "./devices/device", requireTag=True)])

    tags["device"] = TagClass("device",
                              baseclass = "EagleFilePart",
                              attrs=[Attr("name", required=False),
                                     Attr("package", required=False)],
                              sections=[List("connects", "./connects/connect"),
                                        Map("technologies", "./technologies/technology")])

    tags["bus"] = TagClass("bus",
                           baseclass = "EagleFilePart",
                           attrs=[nameAttr],
                           sections = [List("segments", "./segment")])



    tags["net"] = TagClass("net",
                           baseclass = "EagleFilePart",
                           attrs=[nameAttr,
                                  Attr("netclass",
                                       accessorName = "netclass",
                                       xmlName="class",
                                       required=False)],
                           sections = [List("segments", "./segment")])



    tags["signal"] = TagClass("signal",
                              baseclass = "EagleFilePart",
                              attrs=[nameAttr,
                                     Attr("netclass",
                                          accessorName = "netclass",
                                          xmlName="class",
                                          required=False),
                                     Attr("airwireshidden", required=False)],
                              sections = [List("contactrefs", "./contactref"),
                                          List("polygons", "./polygon"),
                                          List("wires", "./wire"),
                                          List("vias", "./via")])



    tags["moduleinst"] = TagClass("moduleinst",
                                  baseclass = "EagleFilePart",
                                  attrs=[nameAttr,
                                         Attr("module", required=True),
                                         Attr("modulevariant", required=False),
                                         xAttr,
                                         yAttr,
                                         Attr("offset", required=False),
                                         Attr("smashed", required=False),
                                         rotAttr])



    tags["variantdef"] = TagClass("variantdef",
                                  baseclass = "EagleFilePart",
                                  attrs=[nameAttr,
                                         Attr("current", required=False)])



    tags["variant"] = TagClass("variant",
                               baseclass = "EagleFilePart",
                               attrs=[nameAttr,
                                      Attr("populate", required=False),
                                      Attr("value", required=False),
                                      Attr("technology", required=False)])



    tags["gate"] = TagClass("gate",
                            baseclass = "EagleFilePart",
                            attrs=[nameAttr,
                                   Attr("symbol", required=True),
                                   xAttr,
                                   yAttr,
                                   Attr("addlevel", required=False),
                                   Attr("swaplevel", required=False)])



    tags["wire"] = TagClass("wire",
                            baseclass = "EagleFilePart",
                            attrs=[Attr("x1", required=True),
                                   Attr("y1", required=True),
                                   Attr("x2", required=True),
                                   Attr("y2", required=True),
                                   Attr("width", required=True),
                                   layerAttr,
                                   Attr("extent", required=False),
                                   Attr("style", required=False),
                                   Attr("curve", required=False),
                                   Attr("cap", required=False)])



    tags["dimension"] = TagClass("dimension",
                                 baseclass = "EagleFilePart",
                                 attrs=[Attr("x1", required=True),
                                        Attr("y1", required=True),
                                        Attr("x2", required=True),
                                        Attr("y2", required=True),
                                        Attr("x3", required=True),
                                        Attr("y3", required=True),
                                        layerAttr,
                                        Attr("dtype", required=False),
                                        Attr("width", required=True),
                                        Attr("extwidth", required=False),
                                        Attr("extlength", required=False),
                                        Attr("extoffset", required=False),
                                        Attr("textsize", required=True),
                                        Attr("textratio", required=False),
                                        Attr("unit", required=False),
                                        Attr("precision", required=False),
                                        Attr("visible", required=False)])



    tags["text"] = TagClass("text",
                            baseclass = "EagleFilePart",
                            preserveTextAs = "text",
                            attrs=[xAttr,
                                   yAttr,
                                   Attr("size", required=True),
                                   layerAttr,
                                   Attr("font", required=False),
                                   Attr("ratio", required=False),
                                   rotAttr,
                                   Attr("align", required=False),
                                   Attr("distance", required=False)])



    tags["circle"] = TagClass("circle",
                              baseclass = "EagleFilePart",
                              attrs=[xAttr,
                                     yAttr,
                                     Attr("radius", required=True),
                                     Attr("width", required=True),
                                     layerAttr])



    tags["rectangle"] = TagClass("rectangle",
                                 baseclass = "EagleFilePart",
                                 attrs=[Attr("x1", required=True),
                                        Attr("y1", required=True),
                                        Attr("x2", required=True),
                                        Attr("y2", required=True),
                                        layerAttr,
                                        rotAttr])



    tags["frame"] = TagClass("frame",
                             baseclass = "EagleFilePart",
                             attrs=[Attr("x1", required=True),
                                    Attr("y1", required=True),
                                    Attr("x2", required=True),
                                    Attr("y2", required=True),
                                    Attr("columns", required=True),
                                    Attr("rows", required=True),
                                    layerAttr,
                                    Attr(
                                         name="border_left",
                                         accessorName="border_left",
                                         xmlName="border-left",
                                         required=False),
                                    Attr(
                                         name="border_right",
                                         accessorName="border_right",
                                         xmlName="border-right",
                                         required=False),
                                    Attr(
                                         name="border_top",
                                         accessorName="border_top",
                                         xmlName="border-top",
                                         required=False),
                                    Attr(
                                         name="border_bottom",
                                         accessorName="border_bottom",
                                         xmlName="border-bottom",
                                         required=False)])



    tags["hole"] = TagClass("hole",
                            baseclass = "EagleFilePart",
                            attrs=[xAttr,
                                   yAttr,
                                   Attr("drill", required=True)])



    tags["pad"] = TagClass("pad",
                           baseclass = "EagleFilePart",
                           attrs=[nameAttr,
                                  xAttr,
                                  yAttr,
                                  Attr("drill", required=True),
                                  Attr("diameter", required=False),
                                  Attr("shape", required=False),
                                  rotAttr,
                                  Attr("stop", required=False),
                                  Attr("thermals", required=False),
                                  Attr("first", required=False)])



    tags["smd"] = TagClass("smd",
                           baseclass = "EagleFilePart",
                           attrs=[nameAttr,
                                  xAttr,
                                  yAttr,
                                  dxAttr,
                                  dyAttr,
                                  layerAttr,
                                  Attr("roundness", required=False),
                                  rotAttr,
                                  Attr("stop", required=False),
                                  Attr("thermals", required=False),
                                  Attr("cream", required=False)])



    tags["element"] = TagClass("element",
                               baseclass = "EagleFilePart",
                               customchild = True,
                               attrs=[nameAttr,
                                      Attr("library", required=True),
                                      Attr("package", required=True),
                                      Attr("value", required=True),
                                      xAttr,
                                      yAttr,
                                      Attr("locked", required=False),
                                      Attr("populate", required=False),
                                      Attr("smashed", required=False),
                                      rotAttr],
                               # Everywhere else we keep attributes in maps,
                               # but this is list because these are actually
                               # drawn on the board.
                               sections = [List("attributes", "./attribute", requireTag=True)])



    tags["via"] = TagClass("via",
                           baseclass = "EagleFilePart",
                           attrs=[xAttr,
                                  yAttr,
                                  Attr("extent", required=True),
                                  Attr("drill", required=True),
                                  Attr("diameter", required=False),
                                  Attr("shape", required=False),
                                  Attr("alwaysstop", required=False)])



    tags["polygon"] = TagClass("polygon",
                               baseclass = "EagleFilePart",
                               attrs=[Attr("width", required=True),
                                      layerAttr,
                                      Attr("spacing", required=False),
                                      Attr("pour", required=False),
                                      Attr("isolate", required=False),
                                      Attr("orphans", required=False),
                                      Attr("thermals", required=False),
                                      Attr("rank", required=False)],
                               sections = [List("vertices", "./vertex")])



    tags["vertex"] = TagClass("vertex",
                              baseclass = "EagleFilePart",
                              attrs=[xAttr,
                                     yAttr,
                                     Attr("curve", required=False)])



    tags["pin"] = TagClass("pin",
                           baseclass = "EagleFilePart",
                           attrs=[nameAttr,
                                  xAttr,
                                  yAttr,
                                  Attr("visible", required=False),
                                  Attr("length", required=False),
                                  Attr("direction", required=False),
                                  Attr("function", required=False),
                                  Attr("swaplevel", required=False),
                                  rotAttr])



    tags["part"] = TagClass("part",
                            baseclass="EagleFilePart",
                            customchild=True,
                            attrs=[nameAttr,
                                   Attr("library", required=True),
                                   Attr("deviceset", required=True),
                                   Attr("device", required=True),
                                   Attr("technology", required=False),
                                   Attr("value", required=False)],
                            sections=[Map("attributes", "./attribute", requireTag=True),
                                      Map("variants", "./variant")])



    tags["port"] = TagClass("port",
                            baseclass = "EagleFilePart",
                            attrs=[nameAttr,
                                   Attr("side", required=True),
                                   Attr("coord", required=True),
                                   Attr("direction", required=False)])



    tags["instance"] = TagClass("instance",
                                baseclass = "EagleFilePart",
                                attrs=[Attr("part", required=True),
                                       Attr("gate", required=True),
                                       xAttr,
                                       yAttr,
                                       Attr("smashed", required=False),
                                       rotAttr],
                                sections= [Map("attributes", "./attribute", requireTag=True)])



    tags["label"] = TagClass("label",
                             baseclass = "EagleFilePart",
                             attrs=[xAttr,
                                    yAttr,
                                    Attr("size", required=True),
                                    layerAttr,
                                    Attr("font", required=False),
                                    Attr("ratio", required=False),
                                    rotAttr,
                                    Attr("xref", required=False)])



    tags["junction"] = TagClass("junction",
                                baseclass = "EagleFilePart",
                                attrs=[xAttr,
                                       yAttr])



    tags["connect"] = TagClass("connect",
                               baseclass = "EagleFilePart",
                               attrs=[Attr("gate", required=True),
                                      Attr("pin", required=True),
                                      Attr("pad", required=True),
                                      Attr("route", required=False)])



    tags["technology"] = TagClass("technology",
                                  baseclass = "EagleFilePart",
                                  attrs=[nameAttr],
                                  sections=[Map("attributes", "./attribute", requireTag=True)])



    tags["attribute"] = TagClass("attribute",
                                 baseclass = "EagleFilePart",
                                 customchild = True,
                                 attrs=[nameAttr,
                                        Attr("value", required=False),
                                        Attr("x", required=False),
                                        Attr("y", required=False),
                                        Attr("size", required=False),
                                        Attr("layer", required=False),
                                        Attr("font", required=False),
                                        Attr("ratio", required=False),
                                        rotAttr,
                                        Attr("display", required=False),
                                        Attr("constant",
                                             type="ConstantAttr",
                                             parse="parse_constant",
                                             unparse="unparse_constant",
                                             required=False)])



    tags["pinref"] = TagClass("pinref",
                              baseclass = "EagleFilePart",
                              attrs=[Attr("part", required=True),
                                     Attr("gate", required=True),
                                     Attr("pin", required=True)])



    tags["contactref"] = TagClass("contactref",
                                  baseclass = "EagleFilePart",
                                  attrs=[Attr("element", required=True),
                                         Attr("pad", required=True),
                                         Attr("route", required=False),
                                         Attr("routetag", required=False)])



    tags["portref"] = TagClass("portref",
                               baseclass = "EagleFilePart",
                               attrs=[Attr("moduleinst", required=True),
                                      Attr("port", required=True)])



    tags["setting"] = TagClass("setting",
                               baseclass = "EagleFilePart",
                               attrs=[Attr("alwaysvectorfont", required=False),
                                      Attr("verticaltext", required=False)])



    tags["designrules"] = TagClass("designrules",
                                   baseclass = "EagleFilePart",
                                   attrs=[nameAttr],
                                   sections=[List("description", "./description", requireTag=True),
                                             Map("params", "./param")])



    tags["grid"] = TagClass("grid",
                            baseclass = "EagleFilePart",
                            attrs=[Attr("distance", required=False),
                                   Attr("unitdist", required=False),
                                   Attr("unit", required=False),
                                   Attr("style", required=False),
                                   Attr("multiple", required=False),
                                   Attr("display", required=False),
                                   Attr("altdistance", required=False),
                                   Attr("altunitdist", required=False),
                                   Attr("altunit", required=False)])



    tags["layer"] = TagClass("layer",
                             baseclass = "EagleFilePart",
                             attrs=[Attr("number", required=True),
                                    nameAttr,
                                    Attr("color", required=True),
                                    Attr("fill", required=True),
                                    Attr("visible", required=False),
                                    Attr("active", required=False)])



    tags["class"] = TagClass("class",
                             baseclass = "EagleFilePart",
                             attrs=[Attr("number", required=True),
                                    nameAttr,
                                    Attr("width", required=False),
                                    Attr("drill", required=False)],
                             sections=[Map("clearances", "./clearance", mapkey="netclass")])



    tags["clearance"] = TagClass("clearance",
                                 baseclass = "EagleFilePart",
                                 attrs=[Attr("netclass",
                                             accessorName = "netclass",
                                             xmlName="class",
                                             required=True),
                                        Attr("value", required=False)])



    tags["description"] = TagClass("description",
                                   baseclass = "EagleFilePart",
                                   preserveTextAs = "text",
                                   attrs=[Attr("language", required=False)])



    tags["param"] = TagClass("param",
                             baseclass = "EagleFilePart",
                             attrs=[nameAttr,
                                    Attr("value", required=True)])



    tags["pass"] = TagClass("pass",
                            baseclass = "EagleFilePart",
                            attrs=[nameAttr,
                                   Attr("refer", required=False),
                                   Attr("active", required=False)],
                            sections=[Map("params", "./param")])



    tags["approved"] = TagClass("approved",
                                baseclass = "EagleFilePart",
                                attrs=[Attr("hash", required=True)])



    tags["sheet"] = TagClass("sheet",
                             baseclass = "EagleFilePart",
                             attrs=[],
                             sections =[Singleton("description", "./description", requireTag=True),
                                        List("plain_elements", "./plain/polygon|./plain/wire|./plain/text|./plain/dimension|./plain/circle|./plain/rectangle|./plain/frame|./plain/hole", requireTag=True),
                                        Map("moduleinsts", "./moduleinsts/moduleinst"),
                                        List("instances", "./instances/instance", requireTag=True),
                                        Map("busses", "./busses/bus", requireTag=True),
                                        Map("nets", "./nets/net", requireTag=True)])



    tags["segment"] = TagClass("segment",
                               baseclass = "EagleFilePart",
                               attrs=[],
                               sections = [List("pinrefs", "./pinref"),
                                           List("portrefs", "./portref"),
                                           List("wires", "./wire"),
                                           List("junctions", "./junction"),
                                           List("labels", "./label")])



    tags["compatibility"] = TagClass("compatibility",
                                     baseclass = "EagleFilePart",
                                     attrs=[],
                                     sections = [List("notes", "./note")])


    tags["eagleBoard"] = TagClass("eagle",
                                  classname="BoardFile",
                                  baseclass="EagleFile",
                                  attrs=[Attr("version", required=True)],
                                  sections=[List("settings", "./drawing/settings/setting",requireTag=True),
                                            Singleton("grid", "./drawing/grid"),
                                            # EagleFile implements layer accessors
                                            Map("layers", "./drawing/layers/layer",suppressAccessors=True, mapkey="number"),
                                            Singleton("description", "./drawing/board/description", requireTag=True),
                                            # We keep all the drawing elements in one container
                                            List("plain_elements", "./drawing/board/plain/polygon|./drawing/board/plain/wire|./drawing/board/plain/text|./drawing/board/plain/dimension|./drawing/board/plain/circle|./drawing/board/plain/rectangle|./drawing/board/plain/frame|./drawing/board/plain/hole", requireTag=True),
                                            Map("libraries", "./drawing/board/libraries/library", requireTag=True),                              
                                            Map("attributes", "./drawing/board/attributes/attribute", requireTag=True),                              
                                            Map("variantdefs", "./drawing/board/variantdefs/variantdef", requireTag=True),
                                            Map("classes", "./drawing/board/classes/class"),
                                            Singleton("designrules", "./drawing/board/designrules"),
                                            Map("autorouter_passes", "./drawing/board/autorouter/pass"),
                                            Map("elements", "./drawing/board/elements/element", requireTag=True),
                                            Map("signals", "./drawing/board/signals/signal", requireTag=True),
                                            List("approved_errors", "./drawing/board/errors/approved"),
                                            Singleton("compatibility", "./compatibility")])


    tags["eagleSchematic"] = TagClass("eagle",
                                      classname="SchematicFile",
                                      baseclass="EagleFile",
                                      attrs=[Attr("version", required=True)],
                                      sections=[List("settings", "./drawing/settings/setting",requireTag=True),
                                                Singleton("grid", "./drawing/grid"),
                                                Map("layers", "./drawing/layers/layer", suppressAccessors=True),
                                                # this is necessary to preserve and provide access to the attributes on the schematic. This object doesn't actually contain anything, though.
                                                Singleton("schematic", "./drawing/schematic"), 
                                                Singleton("description", "./drawing/schematic/description", requireTag=True),
                                                Map("libraries", "./drawing/schematic/libraries/library", requireTag=True),                              
                                                Map("attributes", "./drawing/schematic/attributes/attribute", requireTag=True),                              
                                                Map("variantdefs", "./drawing/schematic/variantdefs/variantdef", requireTag=True),
                                                Map("classes", "./drawing/schematic/classes/class"),
                                                Map("modules", "./drawing/schematic/modules/module"),
                                                Map("parts", "./drawing/schematic/parts/part", requireTag=True),
                                                List("sheets", "./drawing/schematic/sheets/sheet"),
                                                List("approved_errors", "./drawing/schematic/errors/approved"),
                                                Singleton("compatibility", "./compatibility")])

    tags["eagleLibrary"] = TagClass("eagle",
                                    classname="LibraryFile",
                                    baseclass="EagleFile",
                                    attrs=[Attr("version", required=True)],
                                    sections=[List("settings", "./drawing/settings/setting", requireTag=True),
                                              Singleton("grid", "./drawing/grid"),
                                              Map("layers", "./drawing/layers/layer", suppressAccessors=True),
                                              Singleton("library", "./drawing/library"),
                                              Singleton("compatibility", "./compatibility")])

    env = J2.Environment(loader=J2.FileSystemLoader('.'))
    template = env.get_template('HighEagle.jinja.py')

    f = open(args.outfile[0], "w")
    f.write(template.render(tags=tags.values()))

