#!/usr/bin/env python
import jinja2 as J2
import argparse
import logging as log
import copy

# This program generates a set of python classes for manipulating eagle files.
# The process relies on three bodies of information.
#
# 1.  The contents of tag-summary.dat, which is generated from the eagle DTD by
#     the Makefile.  It contains the list of tags and the attributes each one
#     can/must carry.
#
# 2.  The contents of this file.  It specifies the characteristic of each that
#     corresponds to a part of an eagle file.  The file defines several classes
#     (Attr, List,Map,Singleton, and Tag) that specify how the class eagle
#     classes should behave.
#
# 3.  The contents of HighEagle.jinja.py.  This contains the template code for
#     the classes, a base class for all the classes, and a class to represent
#     eagle files, EagleFile.
#
# The classes that this code generates each represent a part of an eagle file
# (class EagleFilePart).  Instances of this class form a tree.  The root of the
# tree is an instance of SchematicFile, BoardFile, or LibraryFile, all of which
# are subclasses of EagleFile.
#
# Each EagleFilePart contains one or more attribute values and one or more
# 'collections' (i.e., lists, maps, or singletons) of EagleFileParts.  For
# instance, SchematicFile contains a collection that maps library names to
# Library objects, a list of Sheet objects, and a singleton Description
# instance.
#
# This file defines the set of collections that each subclass of EagleFilePart
# contains.  Each of these subclasses is represented by a Tag object, which
# contains a list (called "sections") of collections (represented by subclasses
# of Collection -- namely Map, List, and Singleton).  The Tag object also
# includes a list of attributes (represented by class Attr).
#
# Each Attr, Map, List, and Singleton object includes information necessary to
# generate code for it.  This includes mostly pedantic stuff like converting
# "-" to "_" in attribute names so they are valid python identifiers, dealing
# with eagle tag and attribute names that clash with python reserve words, and
# information about which attributes and tags are required and which are
# optional.  There's also some support for parsing values (e.g., converting
# "yes" to True).
#
# The organization of the EagleFilePart hierarchy is similar to the structure
# of the eagle xml file.  However, we make it easier to navigate by flattening
# it somewhat.  For instance, in the eagle file layer defintions live in
# eagle/drawing/layers and sheets live in eagle/drawing/schematic/sheets.  Our
# library "flattens" this hierarchy so that the SchematicFile class has a map of
# layers and a list of sheets.
#
# To realize this flattened structure, we specify the contents of each
# collection using an xpath expression.  All the elements that match the
# expression for Map, List, or Singleton will end up in that collection.  The
# xpath expressions get passed the constructors for the Map,List, and Singleton.
#
# The final stage is to generate the code.  We use the jinja templating system
# for this.  HighEagle.jinja.py contains templates for EagleFilePart subclass.
# It generates code for the constructor, the from_et() method to convert for
# element tree to EagleFileParts, the get_et() method for the reverse
# conversion, a clone() function for copying EagleFileParts, and accessors for
# attributes (get_*() and set_*()) and collections (get_*() and add_*()).
#
# The jinja file also generates a python map called classMap.  This map defines
# the mapping between tag names and EagleFilePart subclasses, and the from_et()
# methods use this map to determine what kind of object to instantiate for a
# given tag.  My manipulating this map, you can extend classes the parser
# generates.  For instance, if you created the class CoolPart(Part) (a subclass
# of Part which represents a <part> tag in an eagle file), set classMap["part"]
# = CoolPart, and then parse an EagleFile, it will be populated with CoolPart
# objects instead of Part objects.  In this way, you can easily extend the
# library which additional functionality.

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a set of classes for manipulating eagle files")
    parser.add_argument("--in", required=True,  type=str, nargs=1, dest='infile', help="tag definition file")
    parser.add_argument("--out", required=True,  type=str, nargs=1, dest='outfile', help="python output")
    args = parser.parse_args()

    log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
    log.info("Verbose output.")

    class Attr:
        """
        Class representing an attribute
        """
        def __init__(self, name, required=False, parse=None, unparse=None):
            self.xmlName = name
            self.accessorName = name
            self.name = name.replace("-", "_")
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
        def __init__(self, name, xpath, adderName=None, itemType=None,suppressAccessors=False, requireTag=False, mapkey=None):
            self.name = name
            self.xpath = xpath
            self.subtag = xpath.split("/")[-1]
            if mapkey is None:
                self.mapkey = "name"
            if adderName is None:
                self.adderName = self.subtag
            else:
                self.adderName = adderName

            self.itemType = itemType
            self.suppressAccessors = suppressAccessors
            self.requireTag = requireTag

    class Map(Collection):
        """
        Collection that maps strings to items
        """
        def __init__(self, name, xpath, adderName=None, itemType=None,suppressAccessors=False, requireTag=False, mapkey=None):
            Collection.__init__(self,name, xpath, adderName, itemType, suppressAccessors, requireTag)
            self.type = "Map"
            if mapkey is None:
                self.mapkey = "name"
            else:
                self.mapkey = mapkey
        

    class List(Collection):
        """
        Collection that is an ordered list
        """
        def __init__(self, name, xpath, adderName=None, itemType=None,suppressAccessors=False, requireTag=False):
            Collection.__init__(self,name, xpath, adderName, itemType, suppressAccessors, requireTag)
            self.type = "List"

    class Singleton(Collection):
        """
        Collection with a single element
        """
        def __init__(self, name, xpath, adderName=None, itemType=None, suppressAccessors=False, requireTag=False):
            Collection.__init__(self,name, xpath, adderName, itemType, suppressAccessors, requireTag)
            self.type = "Singleton"
                
    class TagClass:
        """
        Everything we need to know about an object that can hold the contents of a tag in order ot generate the classes for accessing it.
        """
        def __init__(self,
                     tag,
                     baseclass=None, # what class should you derive from
                     attrs=None,
                     sections=None,
                     customchild = None,  # I will create a subclass of this type for actual use
                     preserveTextAs=""
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
            self.classname = self.get_tag_initial_cap()
            self.customchild = customchild
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
            
        def finalize(self):
            self.maps = [m for m in self.sections if isinstance(m, Map)]
            self.lists = [l for l in self.sections if isinstance(l, List)]
            self.singletons = [s for s in self.sections if isinstance(s, Singleton)]

    # Load attribute information from a file that's generated from the DTD
    spec = open(args.infile[0], "r")
    tags = {}
    for l in spec:
        # parse the line
        name = l.split(":")[0]
        attrs = [x.strip().split() for x in l.split(":")[1].split(",")]
        if len(attrs[0]) == 0:
            attrs = []

        # generate the attributes for each tag.
        tags[name] = TagClass(name,
                         attrs={x[0]: Attr(x[0], required=(x[1] == "REQUIRED")) for x in attrs},
                         baseclass = "EagleFilePart"
                     )

    # clean up attributes that class with python reserve words
    # for t in ["clearance", "net", "signal"]:
    #     tags[t].attrs["class"].accessorName = "class"
    #     tags[t].attrs["class"].xmlName = "class"

    for t in ["clearance", "net", "signal"]:
        tags[t].attrs["class"].name = "netclass"
        tags[t].attrs["class"].accessorName = "netclass"
        tags[t].attrs["class"].xmlName = "class"
    
    for i in ["border-left", "border-top", "border-right", "border-bottom"]:
        tags["frame"].attrs[i].name = i.replace("-", "_")
        tags["frame"].attrs[i].accessorName = i.replace("-", "_")
        tags["frame"].attrs[i].xmlName = i
        
    # add parsing support for layers
    for tag in tags.values():
        if "layer" in tag.attrs:
            tag.attrs["layer"].parse =   "parent.get_root().parse_layer_number"
            tag.attrs["layer"].unparse = "self.get_root().unparse_layer_name"

    # the 'constant' attribute needs to be parsed
    tags["attribute"].attrs["constant"].parse = "parse_constant"
    tags["attribute"].attrs["constant"].unparse = "unparse_constant"

    # Each of the file types gets their own class.  They are all derived from EagleBoardFile
        
    # This section provides a mapping between the contents of this tag and the
    # attributes of this class.  This information maps mostly to the contents
    # of the DTD.  For each collections, the first argument is the name.  The
    # second is the xpath expression that will collect the contents of the
    # collection.
    tags["eagleBoard"] = copy.deepcopy(tags["eagle"])
    tags["eagleBoard"].classname = "BoardFile"
    tags["eagleBoard"].baseclass = "EagleFile"
    tags["eagleBoard"].sections = [List("settings", "./drawing/settings/setting",requireTag=True),
                                   Singleton("grid", "./drawing/grid"),
                                   # EagleFile implements layer accessors
                                   Map("layers", "./drawing/layers/layer",suppressAccessors=True,mapkey="number"),
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
                                   Singleton("compatibility", "./compatibility")]

    # Specification for the SchematicFile class
    tags["eagleSchematic"] = copy.deepcopy(tags["eagle"])
    tags["eagleSchematic"].classname = "SchematicFile"
    tags["eagleSchematic"].baseclass = "EagleFile"
    tags["eagleSchematic"].sections = [List("settings", "./drawing/settings/setting",requireTag=True),
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
                                       Singleton("compatibility", "./compatibility")]
    # and for the library file
    tags["eagleLibrary"] = copy.deepcopy(tags["eagle"])
    #tags["eagleLibrary"].customchild = True
    tags["eagleLibrary"].classname = "LibraryFile"
    tags["eagleLibrary"].baseclass = "EagleFile"
    tags["eagleLibrary"].sections = [List("settings", "./drawing/settings/setting", requireTag=True),
                                     Singleton("grid", "./drawing/grid"),
                                     Map("layers", "./drawing/layers/layer", suppressAccessors=True),
                                     Singleton("library", "./drawing/library"),
                                     Singleton("compatibility", "./compatibility")]

    # we don't need the default class for the eagle tag.
    del tags["eagle"]
    
    tags["module"].sections = [Singleton("description", "./description", requireTag=True),
                               Map("ports", "./ports/port"),
                               Map("variantdefs", "./variantdefs/variantdef", requireTag=True),
                               Map("parts", "./parts/part", requireTag=True),
                               List("sheets", "./sheets/sheet")]

    tags["part"].customchild = True
    tags["part"].sections= [Map("attributes", "./attribute", requireTag=True),
                            Map("variants", "./variant")]

    # customchild means that we will create our own, custum child class for
    # this tag.  This will cause the generated code to define Base_Attribute
    # instead of Attribute.  Then, you can define Attribute yourself by
    # deriving from Base_Attribute
    tags["attribute"].customchild = True
    
    tags["sheet"].sections =[Singleton("description", "./description", requireTag=True),
                             List("plain_elements", "./plain/polygon|./plain/wire|./plain/text|./plain/dimension|./plain/circle|./plain/rectangle|./plain/frame|./plain/hole", requireTag=True),
                             Map("moduleinsts", "./moduleinsts/moduleinst"),
                             List("instances", "./instances/instance", requireTag=True),
                             Map("busses", "./busses/bus", requireTag=True),
                             Map("nets", "./nets/net", requireTag=True)]
                             
    tags["instance"].sections= [Map("attributes", "./attribute", requireTag=True)]

    tags["bus"].sections = [List("segments", "./segment")]

    tags["segment"].sections = [List("pinrefs", "./pinref"),
                                List("portrefs", "./portref"),
                                List("wires", "./wire"),
                                List("junctions", "./junction"),
                                List("labels", "./label")]

    tags["net"].sections = [List("segments", "./segment")]

    tags["library"].sections=[Singleton("description", "./description", requireTag=True),
                              Map("packages", "./packages/package", requireTag=True),
                              Map("symbols", "./symbols/symbol" , requireTag=True),
                              Map("devicesets", "./devicesets/deviceset", requireTag=True)]

    tags["deviceset"].sections=[Singleton("description", "./description", requireTag=True),
                                Map("gates", "./gates/gate", requireTag=True),
                                Map("devices", "./devices/device", requireTag=True)]

    tags["device"].sections=[List("connects", "./connects/connect"),
                             List("technologies", "./technologies/technology")]

    tags["designrules"].sections=[List("description", "./description", requireTag=True),
                                  Map("params", "./param")]
    
    tags["technology"].sections=[Map("attributes", "./attribute", requireTag=True)]
                             
    tags["package"].sections=[Singleton("description", "./description", requireTag=True),
                              List("drawing_elements","./polygon|./wire|./text|./dimension|./circle|./rectangle|./frame|./hole"),
                              Map("pads", "./pad"),
                              Map("smds", "./smd")]
    
    tags["symbol"].sections=[Singleton("description", "./description", requireTag=True),
                             List("drawing_elements","./polygon|./wire|./text|./dimension|./circle|./rectangle|./frame|./hole"),
                             Map("pins", "./pin")]
    
    tags["class"].sections=[Map("clearances", "./clearance", mapkey="netclass")]

    tags["pass"].sections=[Map("params", "./param")]

    tags["element"].customchild = True
    tags["element"].sections = [Map("attributes", "./attribute", requireTag=True)]
    
    tags["signal"].sections = [List("contactrefs", "./contactref"),
                               List("polygons", "./polygon"),
                               List("wires", "./wire"),
                               List("vias", "./via")]

    tags["polygon"].sections = [List("vertices", "./vertex")]
    tags["compatibility"].sections = [List("notes", "./note")]

    tags["description"].preserveTextAs = "text"
    tags["text"].preserveTextAs = "text"
    tags["note"].preserveTextAs = "text"

    
    # finalize() does some post-processing on the sections to prepare them for
    # genearting code.
    for i in tags.values():
        i.finalize()
    
    env = J2.Environment(loader=J2.FileSystemLoader('.'))
    template = env.get_template('HighEagle.jinja.py')

    f = open(args.outfile[0], "w")
    f.write(template.render(tags=tags.values()))

