#!/usr/bin/env python

"""
.. module:: GenerateSwoop

.. moduleauthor:: Steven Swanson (swanson@cs.ucsd.edu)

GenerateSwoop.py generates the file Swoop.py, which contains a set
of python classes for manipulating eagle files.  The process relies on two
bodies of information.

1.  The contents of this file.  It specifies the characteristic of each class
    that corresponds to a part of an eagle file.  The file defines several
    classes (:class:`Attr`, :class:`List`, :class:`Map`, :class:`Singleton`,
    and :class:`TagClass`) that specify how the Eagle classes should behave.

    This file describes a collections of classes that represent a "flattened"
    version of the XML format described in the Eagle DTD.

2.  The contents of Swoop.jinja.py.  This contains the template code for
    the classes, a base class for all the classes, and a class to represent
    eagle files, EagleFile.

The classes that this code generates each represent a part of an eagle file
(class :class:`EagleFilePart`).  Instances of this class form a tree.  The root of the
tree is an instance of :class:`SchematicFile`, :class:`BoardFile`, or :class:`LibraryFile`, all of which
are subclasses of :class:`EagleFile`.

Each :class:`EagleFilePart` contains one or more attributes and one or more
'collections' (i.e., lists, maps, or singletons) of :class:`EagleFilePart` objects.  For
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
for this.  Swoop.jinja.py contains templates for the :class:`EagleFilePart` subclasses.
It generates code for the constructor, the :code:`from_et()` method to convert for
element tree to :class:`EagleFileParts`, the :code:`get_et()` method for the reverse
conversion, a :code:`clone()` function for copying :class:`EagleFileParts`, and accessors for
attributes (:code:`get_*()` and :code:`set_*()`) and collections (:code:`get_*()` and :code:`add_*()`).

Generating Extension to Swoop
=============================

You can also import :code:`GenerateSwoop` as a module.  In this case, it
exposes the a map called :code:`tag` that maps Eagle file XML tag names to
:class:`Tag` objects.  You can then use this information however you would like
to generate extensions to :module:`Swoop`.


"""

import jinja2 as J2
import argparse
import logging as log
import copy
import re

class Attr:
    """
    Class representing an attribute.
    
    """
    def __init__(self, name, required=False, parse=None, unparse=None,vtype=None,accessorName=None,xmlName=None, lookupEFP=None):
        """Create a class describing an attribute.
        
        :param name: The attribute's name.  This is the name used for the member of the :class:`EagleFilePart` object.  For example :code:`foo.netclass` (since :code:`class` clashes with a the Python :code:`class` reserved word.
        :param require: Is the attribute required?
        :param parse: String used to parse to attribute value.  It will be invoked as :code:`parse(x)` where :code:`x` is the contents of the XML attribute.
        :param unparse: String used to unparse the attribute value while generating XML. It will be invoked as :code:`unparse(x)` where :code:`x` is :mod:`Swoop`'s value for the attribute.  :code:'unparse(parse(x))` should be the identity function.
        :param accessorName:This is the string that will appear in Swoop API calls.  For example :code:`foo.get_class()`
        :param xmlName:This is string used in the XML representation.  For example, :code:`class`.
        :param lookupEFP: This is a tuple.  The first element is a type.  The second is a function that looks up an object of that type based on the value of this attribute.  Function should take two arguments, the current :class:`EagleFilePart` and the value of the attribute. 
        """
        self.name = name.replace("-", "_")
        if xmlName is None:
            self.xmlName = name
        else:
            self.xmlName = xmlName
            
            #assert self.xmlName is not None
            #        print "Is " + str(self.name) + " == " + str(self.xmlName) +"?"

        if lookupEFP is None:
            self.lookupEFP = None
        else:
            self.lookupEFP = lookupEFP

        if vtype is None:
            self.vtype = "str"
        else:
            self.vtype = vtype
            
        if accessorName is None:
            self.accessorName = name
        else:
            self.accessorName = accessorName
        self.required = required

        if unparse is None:
            self.unparse = "unparseByType"
        else:
            self.unparse = unparse

        if parse is None:
            self.parse = "parseByType"
        else:
            self.parse = parse

def initialCap(a):
        t = a[0].upper() + a[1:]
        return t

def rstClassify(x):
    return ":class:`" + x + "`"

class Collection:
    """
    Base class for collections.
    """
    def __init__(self, name, xpath, accessorName=None, suppressAccessors=False, requireTag=False, containedTypes=None, dontsort=False):
        """Create a class describing an attribute.

        :param name: The collection's name.  This will be used as the name of the member in the the :code:`EagleFilePart`.
        :param xpath: XPath expression that matches all the tags that should be held in this collection.
        :param suppressAccessors:  If :code:`True`, don't generate accessor functions.
        :param requireTag: This the tag for this collection must appear in the output XML.  The tag that is inserted are the all-but-last tags of xpath expression. For example if :code:`xpath` is :code:`./foo/bar/baz`, the this will ensure that :code:`./foo/bar` exists.
        :param accessorName:This is the string that will appear in Swoop API calls.  For example :code:`foo.get_class()`.  By default, this is the last tag in the xpath.  For example if :code:`xpath` is :code:`foo/bar', the :code:`accessorName` will be :code:`bar`.
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
        if containedTypes is None:
            self.containedTypes = [self.accessorName]
        else:
            self.containedTypes = containedTypes

    def get_contained_type_list_doc_string(self, conjunction="or"):
        if len(self.containedTypes) == 1:
            return rstClassify(initialCap(self.containedTypes[0]))
        else:
            return ", ".join(map(rstClassify , map(initialCap,self.containedTypes[0:-1]))) + " " + conjunction + " " + rstClassify(initialCap(self.containedTypes[-1]))
                                                                                                                 

class Map(Collection):
    """
    Collection that maps strings to items
    """
    def __init__(self, name, xpath, accessorName=None, suppressAccessors=False, requireTag=False, mapkey=None, containedTypes=None):
        """Create a Map object.
        
        See the documentation for :class:`Collection` for the parameters.  There is one additional parameter:
        
        :param mapkey:  This is the attribute of the contained elements that will be used as the index in the map.

        """
        Collection.__init__(self,name, xpath, accessorName,  suppressAccessors, requireTag, containedTypes)
        self.type = "Map"
        if mapkey is None:
            self.mapkey = "name"
        else:
            self.mapkey = mapkey
        

class List(Collection):
    """
    Collection that is an ordered list
    """
    def __init__(self, name, xpath, accessorName=None, suppressAccessors=False, requireTag=False, containedTypes=None):
        """Create a List object.
        
        See the documentation for :class:`Collection` for the parameters. 
        """
        Collection.__init__(self,name, xpath, accessorName,suppressAccessors, requireTag, containedTypes)
        self.type = "List"

class Singleton(Collection):
    """
    Collection with a single element
    """
    def __init__(self, name, xpath, accessorName=None,  suppressAccessors=False, requireTag=False,containedTypes=None):
        """Create a Singleton object.
        
        See the documentation for :class:`Collection` for the parameters. 
        """
        Collection.__init__(self,name, xpath, accessorName,  suppressAccessors, requireTag, containedTypes)
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
                 sections=None,
                 sortattr=None,
                 dontsort=False
    ):
        """
        :param tag: The name of the tag this class is for.
        :param baseclass: The base class to inherit from.
        :param customchild: We will define a child class to implement extra functions, so name the class ``Base_tag`` instead of ``tag``
        :param preserveTextAs: Preserve the text content of the tag in a variable with this name.
        :param attrs: A list of :class:`Attr` objects specifying attributes for the class.
        :param sections: A list of :class:`List`, :class:`Map`, and :class:`Singleton` objects that this class should contain.
        :param dontsort: Don't sort these elements in collections (i.e., order matters)

        """
        if sections is None:
            self.sections = []
        else:
            self.sections = sections

        self.dontsort = dontsort
        self.tag = tag
        self.attrs = attrs
        self.sortattr = sortattr
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

        self.hasCollections = (len(self.maps) + len(self.lists) + len(self.singletons) > 0)
        
    def get_attr_names(self):
        return [x for x in self.attrs]
    def get_list_names(self):
        return [x.name for x in self.lists]
    def get_map_names(self):
        return [x.name for x in self.maps]
    def get_tag_initial_cap(self):
        return initialCap(self.tag)


tags = {}

def layerAttr(required=True):
    return Attr(name="layer",
                vtype="layer_string",
                required=required)

def dimensionAttr(name, required):
    return Attr(name, vtype="float", required=required)

def widthAttr(required):
    return dimensionAttr("width", required)

def drillAttr(required):
    return dimensionAttr("drill", required)

def extwidthAttr(required):
    return dimensionAttr("extwidth", required)
def extlengthAttr(required):
    return dimensionAttr("extlength", required)
def extoffsetAttr(required):
    return dimensionAttr("extoffset", required)
def textsizeAttr(required):
    return dimensionAttr("textsize", required)
def sizeAttr(required):
    return dimensionAttr("size", required)
def diameterAttr(required):
    return dimensionAttr("diameter", required)
def spacingAttr(required):
    return dimensionAttr("spacing", required)
def isolateAttr(required):
    return dimensionAttr("isolate", required)

rotAttr = Attr("rot",
               vtype="str",
               required=False)

def nameAttr():
    return Attr("name",
            vtype="str",
            required=True)

smashedAttr = Attr("smashed", required=False)

tags["note"] = TagClass("note",
                        baseclass = "EagleFilePart",
                        preserveTextAs = "text",
                        attrs=[Attr("minversion", 
                                    required=True),
                               Attr("version",
                                    required=True),
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
                          attrs=[nameAttr(),
                                 Attr("prefix", required=False),
                                 dimensionAttr("dx",True),
                                 dimensionAttr("dy",True)],
                          sections=[Singleton("description", "./description", requireTag=True),
                                    Map("ports", "./ports/port"),
                                    Map("variantdefs", "./variantdefs/variantdef", requireTag=True),
                                    Map("parts", "./parts/part", requireTag=True),
                                    List("sheets", "./sheets/sheet")])

tags["package"] = TagClass("package",
                           baseclass = "EagleFilePart",
                           attrs=[nameAttr()],
                           sections=[Singleton("description", "./description", requireTag=True),
                                     List("drawing_elements","./polygon|./wire|./text|./dimension|./circle|./rectangle|./hole|./frame",
                                          containedTypes=["polygon","wire","text","dimension","circle","rectangle","hole", "frame"],
                                          accessorName="drawing_element"),
                                     Map("pads", "./pad"),
                                     Map("smds", "./smd")])

tags["symbol"] = TagClass("symbol",
                          baseclass = "EagleFilePart",
                          attrs=[nameAttr()],
                          sections=[Singleton("description", "./description", requireTag=True),
                                    List("drawing_elements","./polygon|./wire|./text|./dimension|./circle|./rectangle|./frame|./hole",
                                         containedTypes=["polygon","wire","text","dimension","circle","rectangle","hole"],
                                         accessorName="drawing_element"),
                                    Map("pins", "./pin")])

tags["deviceset"] = TagClass("deviceset",
                             baseclass = "EagleFilePart",
                             attrs=[nameAttr(),
                                    Attr("prefix", required=False),
                                    Attr("uservalue",
                                         vtype="bool",
                                         required=False)],
                             sections=[Singleton("description", "./description", requireTag=True),
                                       Map("gates", "./gates/gate", requireTag=True),
                                       Map("devices", "./devices/device", requireTag=True)])

tags["device"] = TagClass("device",
                          baseclass = "EagleFilePart",
                          attrs=[Attr("name", required=False),
                                 Attr("package",
                                      required=False,
                                      lookupEFP=("Package", "lambda efp, key: efp.get_parent().get_parent().get_package(key)"))],
                          sections=[List("connects", "./connects/connect"),
                                    Map("technologies", "./technologies/technology")])

tags["bus"] = TagClass("bus",
                       baseclass = "EagleFilePart",
                       attrs=[nameAttr()],
                       sections = [List("segments", "./segment")])



tags["net"] = TagClass("net",
                       baseclass = "EagleFilePart",
                       attrs=[nameAttr(),
                              Attr("netclass",
                                   accessorName = "class",
                                   xmlName="class",
                                   required=False)],
                       sections = [List("segments", "./segment")])



tags["signal"] = TagClass("signal",
                          baseclass = "EagleFilePart",
                          attrs=[nameAttr(),
                                 Attr("netclass",
                                      accessorName = "class",
                                      xmlName="class",
                                      required=False,
                                      lookupEFP=("Class", "lambda efp, key: NotImplemented('class lookup from signal not implemented')")),
                                 Attr("airwireshidden", 
                                         vtype="bool",
                                         required=False)],
                          sections = [List("contactrefs", "./contactref"),
                                      List("polygons", "./polygon"),
                                      List("wires", "./wire"),
                                      List("vias", "./via")])



tags["moduleinst"] = TagClass("moduleinst",
                              baseclass = "EagleFilePart",
                              attrs=[nameAttr(),
                                     Attr("module",
                                          required=True,
                                          lookupEFP=("Module","lambda efp, key: NotImplemented('Module lookup not implemented')")),
                                     Attr("modulevariant", required=False),
                                     dimensionAttr("x",True),
                                     dimensionAttr("y",True),
                                     Attr("offset",
                                          vtype="int",
                                          required=False),
                                     smashedAttr,
                                     rotAttr])



tags["variantdef"] = TagClass("variantdef",
                              baseclass = "EagleFilePart",
                              attrs=[nameAttr(),
                                     Attr("current", 
                                          vtype="bool",
                                          required=False)])



tags["variant"] = TagClass("variant",
                           baseclass = "EagleFilePart",
                           attrs=[nameAttr(),
                                  Attr("populate", 
                                       vtype="bool",
                                       required=False),
                                  Attr("value", required=False),
                                  Attr("technology",
                                       required=True)])



tags["gate"] = TagClass("gate",
                        baseclass = "EagleFilePart",
                        attrs=[nameAttr(),
                               Attr("symbol",
                                    required=True,
                                    lookupEFP=("Symbol", "lambda efp, key: efp.get_parent().get_parent().get_symbol(key)")),
                               dimensionAttr("x",True),
                               dimensionAttr("y",True),
                               Attr("addlevel", required=False),
                               Attr("swaplevel",
                                    vtype="int",
                                    required=False)])



tags["wire"] = TagClass("wire",
                        baseclass = "EagleFilePart",
                        attrs=[dimensionAttr("x1", required=True),
                               dimensionAttr("y1", required=True),
                               dimensionAttr("x2", required=True),
                               dimensionAttr("y2", required=True),
                               widthAttr(required=True),
                               layerAttr(required=True),
                               Attr("extent", required=False),
                               Attr("style", required=False),
                               Attr("curve", 
                                    vtype="float",
                                    required=False),
                               Attr("cap", required=False)])



tags["dimension"] = TagClass("dimension",
                             baseclass = "EagleFilePart",
                             attrs=[dimensionAttr("x1", required=True),
                                    dimensionAttr("y1", required=True),
                                    dimensionAttr("x2", required=True),
                                    dimensionAttr("y2", required=True),
                                    dimensionAttr("x3", required=True),
                                    dimensionAttr("y3", required=True),
                                    layerAttr(required=True),
                                    Attr("dtype", required=False),
                                    widthAttr(required=False), # this is in disagreement with the dtd.  However, Eagle generates <dimensions> with no width attribute.  The default seems to be 0.13mm and if that value is selected, the attribute is omitted.
                                    extwidthAttr(required=False),
                                    extlengthAttr(required=False),
                                    extoffsetAttr(required=False),
                                    textsizeAttr(required=True),
                                    Attr("textratio",
                                         vtype="int",
                                         required=False),
                                    Attr("unit", required=False),
                                    Attr("precision",
                                         vtype="int",
                                         required=False),
                                    Attr("visible", 
                                         vtype="bool",
                                         required=False)])



tags["text"] = TagClass("text",
                        baseclass = "EagleFilePart",
                        preserveTextAs = "text",
                        attrs=[dimensionAttr("x",True),
                               dimensionAttr("y",True),
                               sizeAttr(required=True),
                               layerAttr(required=True),
                               Attr("font", required=False),
                               Attr("ratio", 
                                    vtype="int",
                                    required=False),
                               rotAttr,
                               Attr("align", required=False),
                               Attr("distance", 
                                    vtype="int",
                                    required=False)])



tags["circle"] = TagClass("circle",
                          baseclass = "EagleFilePart",
                          attrs=[dimensionAttr("x",required=True),
                                 dimensionAttr("y",required=True),
                                 dimensionAttr("radius", required=True),
                                 widthAttr( required=True),
                                 layerAttr()])



tags["rectangle"] = TagClass("rectangle",
                             baseclass = "EagleFilePart",
                             attrs=[dimensionAttr("x1", required=True),
                                    dimensionAttr("y1", required=True),
                                    dimensionAttr("x2", required=True),
                                    dimensionAttr("y2", required=True),
                                    layerAttr(required=True),
                                    rotAttr])



tags["frame"] = TagClass("frame",
                         baseclass = "EagleFilePart",
                         attrs=[dimensionAttr("x1", required=True),
                                dimensionAttr("y1", required=True),
                                dimensionAttr("x2", required=True),
                                dimensionAttr("y2", required=True),
                                Attr("columns", 
                                     vtype="int",
                                     required=True),
                                Attr("rows",
                                     vtype="int",
                                     required=True),
                                layerAttr(required=True),
                                Attr(name="border_left",
                                     accessorName="border_left",
                                     xmlName="border-left",
                                     vtype="bool",
                                     required=False),
                                Attr(name="border_right",
                                     accessorName="border_right",
                                     xmlName="border-right",
                                     vtype="bool",
                                     required=False),
                                Attr(name="border_top",
                                     accessorName="border_top",
                                     xmlName="border-top",
                                     vtype="bool",
                                     required=False),
                                Attr(name="border_bottom",
                                     accessorName="border_bottom",
                                     xmlName="border-bottom",
                                     vtype="bool",
                                     required=False)])



tags["hole"] = TagClass("hole",
                        baseclass = "EagleFilePart",
                        attrs=[dimensionAttr("x",True),
                               dimensionAttr("y",True),
                               drillAttr( required=True)])



tags["pad"] = TagClass("pad",
                       baseclass = "EagleFilePart",
                       attrs=[nameAttr(),
                              dimensionAttr("x",True),
                              dimensionAttr("y",True),
                              drillAttr( required=True),
                              diameterAttr(required=False),
                              Attr("shape", required=False),
                              rotAttr,
                              Attr("stop",
                                   vtype="bool",
                                   required=False),
                              Attr("thermals",
                                   vtype="bool",
                                   required=False),
                              Attr("first",
                                   vtype="bool",
                                   required=False)])



tags["smd"] = TagClass("smd",
                       baseclass = "EagleFilePart",
                       attrs=[nameAttr(),
                              dimensionAttr("x",True),
                              dimensionAttr("y",True),
                              dimensionAttr("dx",True),
                              dimensionAttr("dy",True),
                              layerAttr(required=True),
                              Attr("roundness", 
                                   vtype="int",
                                   required=False),
                              rotAttr,
                              Attr("stop",
                                   vtype="bool",
                                    required=False),
                              Attr("thermals",
                                   vtype="bool",
                                    required=False),
                              Attr("cream",
                                   vtype="bool",
                                    required=False)])



tags["element"] = TagClass("element",
                           baseclass = "EagleFilePart",
                           #customchild = True,
                           attrs=[nameAttr(),
                                  Attr("library",
                                       required=True,
                                       lookupEFP=("Library", "lambda efp, key: efp.get_parent().get_library(key)")),
                                  Attr("package",
                                       required=True,
                                       lookupEFP=("Package", "lambda efp, key: efp.find_library().get_package(key)")),
                                  Attr("value",
                                       required=True),
                                  dimensionAttr("x",True),
                                  dimensionAttr("y",True),
                                  Attr("locked",
                                       vtype="bool",
                                       required=False),
                                  Attr("populate", 
                                       vtype="bool",
                                       required=False),
                                  smashedAttr,
                                  rotAttr],
                           # I'm not sure if this should be a Map or a
                           # List. There's a board in our test suite that
                           # has two instances of the same attributes. But
                           # what I generate boards like that myself, Eagle
                           # throws an error.  So it's a map for now.
                           sections = [Map("attributes", "./attribute", requireTag=True)])



tags["via"] = TagClass("via",
                       baseclass = "EagleFilePart",
                       attrs=[dimensionAttr("x",True),
                              dimensionAttr("y",True),
                              Attr("extent", required=True),
                              drillAttr( required=True),
                              diameterAttr(required=False),
                              Attr("shape", required=False),
                              Attr("alwaysstop", 
                                   vtype="bool",
                                   required=False)])



tags["polygon"] = TagClass("polygon",
                           baseclass = "EagleFilePart",
                           attrs=[widthAttr( required=True),
                                  layerAttr(required=True),
                                  spacingAttr(required=False),
                                  Attr("pour", required=False),
                                  isolateAttr(required=False),
                                  Attr("orphans",
                                       vtype="bool",
                                       required=False),
                                  Attr("thermals", 
                                       vtype="bool",
                                       required=False),
                                  Attr("rank", 
                                       vtype="int",
                                       required=False)],
                           sections = [List("vertices", "./vertex")])



tags["vertex"] = TagClass("vertex",
                          dontsort=True,
                          baseclass = "EagleFilePart",
                          attrs=[dimensionAttr("x",True),
                                 dimensionAttr("y",True),
                                 Attr("curve", 
                                      vtype="float",
                                      required=False)])



tags["pin"] = TagClass("pin",
                       baseclass = "EagleFilePart",
                       attrs=[nameAttr(),
                              dimensionAttr("x",True),
                              dimensionAttr("y",True),
                              Attr("visible", 
                                   required=False),
                              Attr("length", required=False),
                              Attr("direction", required=False),
                              Attr("function", required=False),
                              Attr("swaplevel", 
                                   vtype="int",
                                   required=False),
                              rotAttr])



tags["part"] = TagClass("part",
                        baseclass="EagleFilePart",
                        customchild=True,
                        attrs=[nameAttr(),
                               Attr("library",
                                    lookupEFP=("Library", "lambda efp, key: efp.get_parent().get_library(key)"),
                                    required=True),
                               Attr("deviceset",
                                    lookupEFP=("Deviceset", "lambda efp, key: efp.find_library().get_deviceset(key)"),
                                    required=True),
                               Attr("device",
                                    lookupEFP=("Device", "lambda efp, key: efp.find_deviceset().get_device(key)"),
                                    required=True),
                               Attr("technology",
                                    lookupEFP=("Technology","lambda efp, key: efp.find_device().get_technology(key)"),
                                    required=False,
                                    vtype="None_is_empty_string"),
                               Attr("value", required=False)],
                        sections=[Map("attributes", "./attribute", requireTag=True),
                                  Map("variants", "./variant")])



tags["port"] = TagClass("port",
                        baseclass = "EagleFilePart",
                        attrs=[nameAttr(),
                               Attr("side", 
                                    vtype="int",
                                    required=True),
                               Attr("dimension", required=True),
                               Attr("direction", required=False)])



tags["instance"] = TagClass("instance",
                            baseclass = "EagleFilePart",
                            attrs=[Attr("part",
                                        lookupEFP=("Part","lambda efp, key: NotImplemented('Lookup of part from instance not implemented.')"),
                                        required=True),
                                   Attr("gate",
                                        lookupEFP=("Gate","lambda efp, key: NotImplemented('Lookup of gate from instance not implemented.')"),
                                        required=True),
                                   dimensionAttr("x",True),
                                   dimensionAttr("y",True),
                                   smashedAttr,
                                   rotAttr],
                            sections= [Map("attributes", "./attribute", requireTag=True)])



tags["label"] = TagClass("label",
                         baseclass = "EagleFilePart",
                         attrs=[dimensionAttr("x",True),
                                dimensionAttr("y",True),
                                sizeAttr(required=True),
                                layerAttr(required=True),
                                Attr("font", required=False),
                                Attr("ratio",
                                     vtype="int",
                                      required=False),
                                rotAttr,
                                Attr("xref", 
                                     vtype="bool",
                                     required=False)])



tags["junction"] = TagClass("junction",
                            baseclass = "EagleFilePart",
                            attrs=[dimensionAttr("x",True),
                                   dimensionAttr("y",True)])



tags["connect"] = TagClass("connect",
                           baseclass = "EagleFilePart",
                           attrs=[Attr("gate",
                                       lookupEFP=("Gate","lambda efp, key: NotImplemented('Lookup of gate from connect not implemented.')"),
                                       required=True),
                                  Attr("pin",
                                       lookupEFP=("Pin","lambda efp, key: NotImplemented('Lookup of pin from connect not implemented.')"),
                                       required=True),
                                  Attr("pad",
                                       lookupEFP=("Pad","lambda efp, key: NotImplemented('Lookup of pad from connect not implemented.')"),
                                       required=True),
                                  Attr("route", required=False)])



tags["technology"] = TagClass("technology",
                              baseclass = "EagleFilePart",
                              attrs=[nameAttr()],
                              sections=[Map("attributes", "./attribute", requireTag=True)])



tags["attribute"] = TagClass("attribute",
                             baseclass = "EagleFilePart",
                             customchild = True,
                             attrs=[nameAttr(),
                                    Attr("value", required=False),
                                    dimensionAttr("x", required=False),
                                    dimensionAttr("y", required=False),
                                    sizeAttr(required=False),
                                    layerAttr(required=False),
                                    Attr("font", required=False),
                                    Attr("ratio",
                                         vtype="int",
                                         required=False),
                                    rotAttr,
                                    Attr("display", required=False),
                                    Attr("align", required=False), # SS: not in the standard DTD
                                    Attr("constant",
                                         vtype="constant_bool",
                                         required=False)])



tags["pinref"] = TagClass("pinref",
                          baseclass = "EagleFilePart",
                          attrs=[Attr("part",
                                      lookupEFP=("Part","lambda efp, key: NotImplemented('Lookup of part from pinref not implemented.')"),
                                      required=True),
                                 Attr("gate",
                                      lookupEFP=("Gate","lambda efp, key: NotImplemented('Lookup of gate from pinref not implemented.')"),
                                      required=True),
                                 Attr("pin",
                                      lookupEFP=("Pin", "lambda efp, key: NotImplemented('Lookup of pin from pinref not implemented.')"),
                                      required=True)])



tags["contactref"] = TagClass("contactref",
                              baseclass = "EagleFilePart",
                              attrs=[Attr("element",
                                          lookupEFP=("Element","lambda efp, key: NotImplemented('Lookup of element from contactref not implemented.')"),
                                          required=True),
                                     Attr("pad",
                                          lookupEFP=("Pad","lambda efp, key: NotImplemented('Lookup of pad from contactref not implemented.')"),
                                          required=True),
                                     Attr("route", required=False),
                                     Attr("routetag", required=False)])



tags["portref"] = TagClass("portref",
                           baseclass = "EagleFilePart",
                           attrs=[Attr("moduleinst",
                                       lookupEFP=("Moduleinst","lambda efp, key: NotImplemented('Lookup of moduleinst from portref not implemented.')"),
                                       required=True),
                                  Attr("port",
                                       lookupEFP=("Port", "lambda efp, key: NotImplemented('Lookup of port from portref not implemented.')"),
                                       required=True)])



tags["setting"] = TagClass("setting",
                           baseclass = "EagleFilePart",
                           attrs=[Attr("alwaysvectorfont", 
                                       vtype="bool",
                                       required=False),
                                  Attr("verticaltext", required=False)])



tags["designrules"] = TagClass("designrules",
                               baseclass = "EagleFilePart",
                               attrs=[nameAttr()],
                               sections=[List("description", "./description", requireTag=True),
                                         Map("params", "./param")])



tags["grid"] = TagClass("grid",
                        baseclass = "EagleFilePart",
                        attrs=[Attr("distance",
                                    vtype="float",
                                    required=False),
                               Attr("unitdist", required=False),
                               Attr("unit", required=False),
                               Attr("style", required=False),
                               Attr("multiple", 
                                     vtype="int",
                                     required=False),
                               Attr("display",
                                    vtype="bool",
                                    required=False),
                               Attr("altdistance",
                                    vtype="float",
                                    required=False),
                               Attr("altunitdist", required=False),
                               Attr("altunit", required=False)])



tags["layer"] = TagClass("layer",
                         baseclass = "EagleFilePart",
                         sortattr="number",
                         attrs=[Attr("number",
                                     vtype="int",
                                     required=True),
                                nameAttr(),
                                Attr("color", 
                                     vtype="int",
                                     required=True),
                                Attr("fill", 
                                     vtype="int",
                                     required=True),
                                Attr("visible", 
                                     vtype="bool",
                                     required=False),
                                Attr("active", 
                                     vtype="bool",
                                     required=False)])



tags["class"] = TagClass("class",
                         baseclass = "EagleFilePart",
                         attrs=[Attr("number", required=True),
                                nameAttr(),
                                widthAttr(required=False),
                                drillAttr(required=False)],
                         sections=[Map("clearances", "./clearance", mapkey="netclass")])



tags["clearance"] = TagClass("clearance",
                             baseclass = "EagleFilePart",
                             attrs=[Attr("netclass",
                                         accessorName = "class",
                                         xmlName="class",
                                         lookupEFP=("Class","lambda efp, key: NotImplemented('Lookup of class from clearance not implemented.')"),
                                         required=True),
                                    dimensionAttr("value", required=False)])



tags["description"] = TagClass("description",
                               baseclass = "EagleFilePart",
                               preserveTextAs = "text",
                               attrs=[Attr("language", required=False)])



tags["param"] = TagClass("param",
                         baseclass = "EagleFilePart",
                         attrs=[nameAttr(),
                                Attr("value", required=True)])



tags["pass"] = TagClass("pass",
                        baseclass = "EagleFilePart",
                        attrs=[nameAttr(),
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
                                    List("plain_elements", "./plain/polygon|./plain/wire|./plain/text|./plain/dimension|./plain/circle|./plain/rectangle|./plain/frame|./plain/hole",
                                         containedTypes=["polygon","wire","text","dimension","circle","rectangle","frame","hole"],
                                         accessorName="plain_element",
                                         requireTag=True),
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
                              attrs=[Attr("version",
                                          required=True)],
                              sections=[List("settings", "./drawing/settings/setting",requireTag=True),
                                        Singleton("grid", "./drawing/grid"),
                                        # EagleFile implements layer accessors
                                        Map("layers", "./drawing/layers/layer",suppressAccessors=True, mapkey="number"),
                                        Singleton("description", "./drawing/board/description", requireTag=True),
                                        # We keep all the drawing elements in one container
                                        List("plain_elements", "./drawing/board/plain/polygon|./drawing/board/plain/wire|./drawing/board/plain/text|./drawing/board/plain/dimension|./drawing/board/plain/circle|./drawing/board/plain/rectangle|./drawing/board/plain/frame|./drawing/board/plain/hole",
                                             containedTypes=["polygon","wire","text","dimension","circle","rectangle","frame","hole"],
                                             accessorName="plain_element",
                                             requireTag=True),
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
                                customchild=True,
                                attrs=[Attr("version", required=True)],
                                sections=[List("settings", "./drawing/settings/setting", requireTag=True),
                                          Singleton("grid", "./drawing/grid"),
                                          Map("layers", "./drawing/layers/layer", suppressAccessors=True),
                                          Singleton("library", "./drawing/library"),
                                          Singleton("compatibility", "./compatibility")])

def main(filename):
    log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
    log.info("Verbose output.")

    env = J2.Environment(loader=J2.FileSystemLoader('.'))
    template = env.get_template('Swoop.py.jinja')

    f = open(filename, "w")

    out = template.render(tags=tags.values())
    lines = out.split("\n")

    for l in lines:
        if not re.match("^\s*#\s*$", l):
            f.write(l)
            f.write("\n")
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a set of classes for manipulating eagle files")
    parser.add_argument("--out", required=True,  type=str, nargs=1, dest='outfile', help="python output")
    args = parser.parse_args()
    main(args.outfile[0])
