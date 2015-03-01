#!/usr/bin/env python
import jinja2 as J2
import argparse
import logging as log
import copy

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate functions for building Eagle tags")
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
            self.xml_name = name
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
        def __init__(self, name, xpath, adderName=None, itemType=None,suppressAccessors=False):
            self.name = name
            self.xpath = xpath
            self.subtag = xpath.split("/")[-1]
            if adderName is None:
                self.adderName = self.subtag
            else:
                self.adderName = adderName

            self.itemType = itemType
            self.suppressAccessors = suppressAccessors

    class Map(Collection):
        """
        Collection that maps strings to items
        """
        def __init__(self, name, xpath, adderName=None, itemType=None,suppressAccessors=False):
            Collection.__init__(self,name, xpath, adderName, itemType, suppressAccessors)
            self.type = "Map"

    class List(Collection):
        """
        Collection that is an ordered list
        """
        def __init__(self, name, xpath, adderName=None, itemType=None,suppressAccessors=False):
            Collection.__init__(self,name, xpath, adderName, itemType, suppressAccessors)
            self.type = "List"

    class Singleton(Collection):
        """
        Collection with a single element
        """
        def __init__(self, name, xpath, adderName=None, itemType=None, suppressAccessors=False):
            Collection.__init__(self,name, xpath, adderName, itemType, suppressAccessors)
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
                     customchild = None  # I will create a subclass of this type for actual use
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
    for t in ["clearance", "net","signal"]:
        tags[t].attrs["class"].name = "netclass"
        tags[t].attrs["class"].xmlName = "class"

    # add parsing support for layers
    for tag in tags.values():
        if "layer" in tag.attrs:
            tag.attrs["layer"].parse =   "parent.get_root().parse_layer_number"
            tag.attrs["layer"].unparse = "self.get_root().unparse_layer_name"

    # the 'constant' attribute needst to be parsed
    tags["attribute"].attrs["constant"].parse = "parse_constant"
    tags["attribute"].attrs["constant"].unparse = "unparse_constant"

    # Each of the file types gets their own class.  They are all derived from EagleBoardFile
    tags["eagleBoard"] = copy.deepcopy(tags["eagle"])
    tags["eagleBoard"].classname = "BoardFile"
    tags["eagleBoard"].baseclass = "EagleFile"
    # This section provides a mapping between the contents of this tag and the
    # attributes of this class.  This information maps mostly to the contents
    # of the DTD.  For each collections, the first argument is the name.  The
    # second is the xpath expression that will collect the contents of the
    # collection.
    tags["eagleBoard"].sections = [List("settings", "./drawing/settings/setting"),
                                   Singleton("grid", "./drawing/grid"),
                                   # EagleFile implements layer accessors
                                   Map("layers", "./drawing/layers/layer",suppressAccessors=True),
                                   Singleton("description", "./drawing/board/description"),
                                   # We keep all the drawing elements in one container
                                   List("plain_elements", "./drawing/board/plain/polygon|./drawing/board/plain/wire|./drawing/board/plain/text|./drawing/board/plain/dimension|./drawing/board/plain/circle|./drawing/board/plain/rectangle|./drawing/board/plain/frame|./drawing/board/plain/hole"),
                                   Map("libraries", "./drawing/board/libraries/library"),                              
                                   Map("attributes", "./drawing/board/attributes/attribute"),                              
                                   Map("variantdefs", "./drawing/board/variantdefs/variantdef"),
                                   Map("classes", "./drawing/board/classes/class"),
                                   Singleton("designrules", "./drawing/board/designrules"),
                                   Map("autorouter_passes", "./drawing/board/autorouter/pass"),
                                   Map("elements", "./drawing/board/elements/element"),
                                   Map("signals", "./drawing/board/signals/signal"),
                                   List("approved_errors", "./drawing/board/errors/approved")]

    # Specification for the SchematicFile class
    tags["eagleSchematic"] = copy.deepcopy(tags["eagle"])
    tags["eagleSchematic"].classname = "SchematicFile"
    tags["eagleSchematic"].baseclass = "EagleFile"
    tags["eagleSchematic"].sections = [List("settings", "./drawing/settings/setting"),
                                       Singleton("grid", "./drawing/grid"),
                                       Map("layers", "./drawing/layers/layer", suppressAccessors=True),
                                       Singleton("description", "./drawing/schematic/description"),
                                       Map("libraries", "./drawing/schematic/libraries/library"),                              
                                       Map("attributes", "./drawing/schematic/attributes/attribute"),                              
                                       Map("variantdefs", "./drawing/schematic/variantdefs/variantdef"),
                                       Map("classes", "./drawing/schematic/classes/class"),
                                       Map("modules", "./drawing/schematic/modules/module"),
                                       Map("parts", "./drawing/schematic/parts/part"),
                                       List("sheets", "./drawing/schematic/sheets/sheet"),
                                       List("approved_errors", "./drawing/schematic/errors/approved")]
    # and for the library file
    tags["eagleLibrary"] = copy.deepcopy(tags["eagle"])
    tags["eagleLibrary"].classname = "LibraryFile"
    tags["eagleLibrary"].baseclass = "EagleFile"
    tags["eagleLibrary"].sections = [List("settings", "./drawing/settings/setting"),
                                     Singleton("grid", "./drawing/grid"),
                                     Map("layers", "./drawing/layers/layer", suppressAccessors=True),
                                     Singleton("library", "./drawing/library")]

    # we don't need the default class for the eagle tag.
    del tags["eagle"]
    
    tags["module"].sections = [Singleton("description", "./description"),
                               Map("ports", "./ports/port"),
                               Map("variantdefs", "./variantdefs/variantdef"),
                               Map("parts", "./parts/part"),
                               List("sheets", "./sheets/sheet")]

    tags["part"].customchild = True
    tags["part"].sections= [Map("attributes", "./attribute"),
                            Map("variants", "./variant")]

    # customchild means that we will create our own, custum child class for
    # this tag.  This will cause the generated code to define Base_Attribute
    # instead of Attribute.  Then, you can define Attribute yourself by
    # deriving from Base_Attribute
    tags["attribute"].customchild = True
    
    tags["sheet"].sections =[Singleton("description", "./description"),
                             List("plain_elements", "./plain/polygon|./plain/wire|./plain/text|./plain/dimension|./plain/circle|./plain/rectangle|./plain/frame|./plain/hole"),
                             Map("moduleinsts", "./moduleinsts/moduleinst"),
                             List("instances", "./instances/instance"),
                             Map("busses", "./busses/bus"),
                             Map("nets", "./nets/net")]
                             
    tags["instance"].sections= [Map("attributes", "./attribute")]

    tags["bus"].sections = [List("segments", "./segment")]

    tags["segment"].sections = [List("pinrefs", "./pinref"),
                                List("portrefs", "./portref"),
                                List("wires", "./wire"),
                                List("junctions", "./junction"),
                                List("labels", "./label")]

    tags["net"].sections = [List("segments", "./segment")]
    
    tags["library"].sections=[Singleton("description", "./description"),
                              Map("packages", "./packages/package"),
                              Map("symbols", "./symbols/symbol" ),
                              Map("devicesets", "./devicesets/deviceset")]

    tags["deviceset"].sections=[Singleton("description", "./description"),
                                Map("gates", "./gates/gate"),
                                Map("devices", "./devices/device")]

    tags["device"].sections=[List("connects", "./connects/connect"),
                          List("technologies", "./technologies/technology")]

    tags["designrules"].sections=[Singleton("description", "./description"),
                                  Map("params", "./param")]
    
    tags["technology"].sections=[Map("attributes", "./attributes/attribute")]
                             
    tags["package"].sections=[Singleton("description", "./description"),
                              List("drawing_elements","./polygon|./wire|./text|./dimension|./circle|./rectangle|./frame|./hole"),
                              Map("pads", "./pad"),
                              Map("smds", "./smd"),
                          ]
    tags["symbol"].sections=[Singleton("description", "./description"),
                              List("drawing_elements","./polygon|./wire|./text|./dimension|./circle|./rectangle|./frame|./hole"),
                              Map("pins", "./pin")]
    
    tags["class"].sections=[Map("clearances", "./clearance")]

    tags["pass"].sections=[Map("params", "./param")]

    tags["element"].customchild = True
    tags["element"].sections = [Map("attributes", "./attribute")]
    
    tags["signal"].sections = [List("contactrefs", "./contactref"),
                               List("polygons", "./polygon"),
                               List("wires", "./wire"),
                               List("vias", "./via")]

    tags["polygon"].sections = [List("vertices", "./vertex")]

    # finalize() does some post-processing on the sections to prepare them for
    # genearting code.
    for i in tags.values():
        i.finalize()
    
    env = J2.Environment(loader=J2.FileSystemLoader('.'))
    template = env.get_template('HighEagle.jinja.py')

    f = open(args.outfile[0], "w")
    f.write(template.render(tags=tags.values()))

