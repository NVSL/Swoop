#from HighEagle import *
from lxml import etree as ET
import eagleDTD
import StringIO
import logging as log
import copy

class EagleFormatError (Exception):
    def __init__(self, text=""):
        self.text = text
    def __str__(self):
        return self.text

class HighEagleError (Exception):
    def __init__(self, text):
        self.text = text
    def __str__(self):
        return self.text

class EagleFilePart(object):
    def __init__(self):
        self.parent = None

    def get_file(self):
        r = self.get_root()
        if isinstance(r, EagleFile):
            return r
        else:
            return None

    def get_parent(self):
        return self.parent

    def from_et ():
        raise NotImplementedError()
    
    def get_et ():
        raise NotImplementedError()

    def get_root(self):
        if self.get_parent() is not None:
            return self.get_parent().get_root()
        else:
            return self

    def clone(self):
        """
        Clone the EagleFilePart.  It should be identical to the orginial, except that the parent should be None
        """
        raise NotImplementedError()

    def is_child(self, f):
        if f == "parent":
            return False
        else:
            return True

    def get_children(self):
        raise NotImplementedError()

    def check_sanity(self):
        for i in self.get_children():
            #print "."
            if i.parent != self:
                raise HighEagleError("Parent pointer mismatch.  Child = " + str(i) + "; child.parent = " + str(i.parent) + "; Parent = " + str(self) )
            i.check_sanity()

class EaglePartVisitor(object):

    def __init__(self, root=None):
        self.root = root

    def go(self):
        self.visit(self.root)
        return self
    
    def visitFilter(self, e):
        return True

    def decendFilter(self, e):
        return True

    def default_post(self,e):
        pass

    def default_pre(self,e):
        pass

    def visit(self, efPart):
        if self.visitFilter(efPart):
            try:
                pre = getattr(self,type(efPart).__name__ + "_pre")
                pre(efPart)
            except AttributeError:
                self.default_pre(efPart)

        if self.decendFilter(efPart):
            for e in efPart.get_children():        
                self.visit(e)
                
        if self.visitFilter(efPart):
            try:
                post = getattr(self,type(efPart).__name__ + "_post")
                post(efPart)
            except AttributeError:
                self.default_post(efPart)

# class DrawingElement (EagleFilePart):
#     """
#     EAGLE drawing tag.
#     This is an abstract tag that is used for wire, rectangle, circle, etc.
#     """
    
#     def __init__(self):
#         EagleFilePart.__init__(self)

#     @staticmethod
#     def from_et (drawing_root):
#         if drawing_root.tag == "polygon":
#             return Polygon.from_et(drawing_root)
#         elif drawing_root.tag == "wire":
#             return Wire.from_et(drawing_root)
#         elif drawing_root.tag == "text":
#             return Text.from_et(drawing_root)
#         elif drawing_root.tag == "dimension":
#             return Dimension.from_et(drawing_root)
#         elif drawing_root.tag == "circle":
#             return Circle.from_et(drawing_root)
#         elif drawing_root.tag == "rectangle":
#             return Rectangle.from_et(drawing_root)
#         elif drawing_root.tag == "frame":
#             return Frame.from_et(drawing_root)
#         elif drawing_root.tag == "hole":
#             return Hole.from_et(drawing_root)
#         else:
#             raise Exception("Don't know how to parse "+drawing_root.tag+" tag as a drawing tag.")        

class EagleFile(EagleFilePart):

    DTD = ET.DTD(StringIO.StringIO(eagleDTD.DTD))

    def __init__ (self):
        EagleFilePart.__init__(self)
        self.filename= None
        self.root = None
        self.tree = None
        self.layersByNumber = {}
        self.layers = {}
        
    def validate(self):
        v = EagleFile.DTD.validate(self.get_et())
        
        if not v:
            log.warning("Eagle file opened as '" + str(self.filename) +"' is invalid: " + str(EagleFile.DTD.error_log.filter_from_errors()[0]))
        else:
            log.info("Eagle file opened as '" + self.filename +"' is valid.")
        return v

    @staticmethod
    def from_file (filename):
        """
        Loads a Eagle file from a .sch, .lbr, or .brd file.
        """
        tree = ET.parse(filename)
        root = tree.getroot()
        
        if filename[-4:] == ".sch":
            ef = SchematicFile.from_et(root)
        elif filename[-4:] == ".brd":
            ef = BoardFile.from_et(root)
        elif filename[-4:] == ".lbr":
            ef = LibraryFile.from_et(root)#,filename=filename)
        else:
            raise HighEagleError("Unknown file suffix: '" + filename[-4:] + "'")
        ef.filename = filename
        ef.root = root
        ef.tree = tree
        
        ef.check_sanity()
        return ef

    @staticmethod
    def from_file_by_type(filename, ftype):
        n = EagleFile.from_file(filename)
        if not isinstance(n, ftype):
            raise HighEagleError("File is '" + filename + "' is not " + ftype.__name__)
        return n

    def write (self, filename):
        """
        Exports the Schematic to an EAGLE schematic file.
        
        """
        header="""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE eagle SYSTEM "eagle.dtd">
"""
        self.check_sanity()
        if not self.validate():
            f = open(filename + ".broken.xml", "w")
            f.write(header + ET.tostring(ET.ElementTree(self.get_et()),pretty_print=True))
            raise HighEagleError("element tree does not validate" + str(EagleFile.DTD.error_log.filter_from_errors()[0]))
        else:
            f = open(filename, "w")
            f.write(header+ET.tostring(ET.ElementTree(self.get_et()),pretty_print=True))

    def add_layer (self, layer):
        assert isinstance(layer, Layer)
        #print str(self) +" " + str(int(layer.number))
        self.layersByNumber[int(layer.number)] = layer
        self.layers[layer.name] = layer
        layer.parent = self

    def get_layers(self):
        return self.layers

    def get_layersByNumber(self):
        return self.layersByNumber

    # def get_flippedLayer(self, l):
    #     if (isinstance(l, str)):
    #         origName = l
    #         if l[0] == "t":
    #             l = "b" + l[1:]
    #         elif l[0] == "b":
    #             l = "t" + l[1:]
    #         elif l == "Top":
    #             l = "Bottom"
    #         elif l == "Bottom":
    #             l = "Top"
    #         if l not in self.layers:
    #             raise HighEagleError("Tried to flip layer '" + origName + "', but '" + l + "' doesn't exist")
    #         return name
    #     elif (isinstance(l,int)):
    #         if l in self.layersByNumber:
    #             return self.get_flippedLayer(self, self.layersByNumber[l]).number
    #         else:
    #             raise HighEagleError("Can't find layer number " + number)
    #     elif (isinstance(l,Layer)):
    #         if l.name in self.layers:
    #             return self.layers[get_flippedLayer(l.name)]
    #         else:
    #             raise HighEagleError("Can't find layer '" + l.name +"' in this file")

    def parse_layer_number(self, num):
        if num is None:
            return None
        return self.layer_number_to_name(num)

    def unparse_layer_name(self, name):
        if name is None:
            return None
        return self.layer_name_to_number(name)
    
    def layer_number_to_name(self, num):
        n = int(num)
        if n not in self.layersByNumber:
            #print self
            raise HighEagleError("No layer number " + str(n))
        return self.layersByNumber[n].name

    def layer_name_to_number(self, name):
        assert type(name) is str
        if name not in self.layers:
            raise HighEagleError("No layer named '" + name + "' in " + self.filename)
        return self.layers[name].number

    def remove_layer(self, layer):
        if type(layer) is str:
            l = self.layers[layer]
            self.remove_layer(l)
        elif type(layer) is int:
            l = self.layersByNumber[layer]
            self.remove_layer(l)
        elif isinstance(layer, Layer):
            self.layers[layer.name].parent = None
            del self.layers[layer.name]
            del self.layersByNumber[int(layer.number)]
        else:
            raise HighEagleError("Invalid layer spec: " + str(layer))
            
    # def get_manifest(self):
    #     raise NotImplementedError("Manifest for " + str(type(self)))

    def find_library_by_name(self, l):
        return self.libraries.get(l)

    
def smartAddSubTags(root, path):
    pathSegments = path.split("|")[0].replace("./","").split("/")
    target = root
    for p in pathSegments[0:-1]:
        new_target = target.find(p)
        if new_target is None:
            target = ET.SubElement(target,p)
        else:
            target = new_target
    return target

classMap = {}

def parse_constant(s):
    return s != "no"

def unparse_constant(s):
    if not s:
        return "no"
    else:
        return "yes"
    
#{% for tag in tags %}

#{%if not tag.customchild %}
#{% set classname = tag.classname %}
#{% else %}
#{% set classname = "Base_" + tag.classname %}
#{%endif%}

class {{classname}}({{tag.baseclass}}):
    def __init__(self,
                 #{%for a in tag.attrs.values() %}
                 {{a.name}}=None,
                 #{%endfor%}
                 #{%for l in tag.sections %}
                 {{l.name}}=None,
                 #{%endfor%}
                ):
        {{tag.baseclass}}.__init__(self)
        
        #{%for a in tag.attrs.values() %}
        #if {{a.name}} is not None:
        self.{{a.name}} = {{a.name}}
        #{%if a.required %}
        #else:
        #    self.{{a.name}} = None
        #{%endif%}    

        #{%endfor%}

        #{%for l in tag.lists %}
        if {{l.name}} is None:
            self.{{l.name}} = []
        else:
            self.{{l.name}} = {{l.name}}
        #{%endfor%}

        #{%for m in tag.maps %}
        if {{m.name}} is None:
            self.{{m.name}} = {}
        else:
            self.{{m.name}} = {{m.name}}
        #{%endfor%}

        #{%for s in tag.singletons%}
        self.{{s.name}} = {{s.name}}
        #{%endfor%}

    @classmethod
    def from_et(cls,root,parent=None):
        assert root.tag == "{{tag.tag}}"
        n = cls(
            #{%for a in tag.attrs.values()%}
            #{%if a.parse != "" %}
            {{a.name}}={{a.parse}}(root.get("{{a.name}}")),
            #{%else%}
            {{a.name}}=root.get("{{a.name}}"),
            #{%endif%}
            #{%endfor%}
        )
        n.parent = parent
        #{%for m in tag.maps%}
        for c in root.xpath("{{m.xpath}}"):
            n.add_{{m.adderName}}(classMap[c.tag].from_et(c, n))
            #n.{{m.name}}[c.get("name")] =  classMap[c.tag].from_et(c, n)
            
        #{%endfor%}
        #{%for l in tag.lists %}
        for c in root.xpath("{{l.xpath}}"):
            n.add_{{l.adderName}}(classMap[c.tag].from_et(c,n))
            #n.{{l.name}} = [classMap[c.tag].from_et(c,n) for 
        #{%endfor%}
        #{%for s in tag.singletons %}
        x = root.xpath("{{s.xpath}}")
        if len(x) is not 0:
            n.set_{{s.adderName}}(classMap[x[0].tag].from_et(x[0],n))
        #{%endfor%}
        return n


    def get_et(self):
        r = ET.Element("{{tag.tag}}")
        #{%for a in tag.attrs.values()%}
        #{%if a.required %}
        if self.{{a.name}} is None:
            #{%if a.unparse != "" %}
            r.set("{{a.xml_name}}", {{a.unparse}}(None))
            #{%else%}
            r.set("{{a.xml_name}}", "")
            #{%endif%}
        else:
            #{%if a.unparse != "" %}
            r.set("{{a.xml_name}}", {{a.unparse}}(self.{{a.name}}))
            #{%else%}
            r.set("{{a.xml_name}}", self.{{a.name}})
            #{%endif%}
        #{%else%}
        if self.{{a.name}} is not None:
            #{%if a.unparse != "" %}
            r.set("{{a.xml_name}}", {{a.unparse}}(self.{{a.name}}))
            #{%else%}
            r.set("{{a.xml_name}}", self.{{a.name}})
            #{%endif%}
        #{%endif%}g
        #{%endfor%}
        
        #{%for l in tag.sections%}
        #{%if l.type == "List" %}
        if len(self.{{l.name}}) is not 0:
            target = smartAddSubTags(r, "{{l.xpath}}")
            target.extend([i.get_et() for i in self.{{l.name}}])
        #{%elif l.type == "Map" %}
        if len(self.{{l.name}}) is not 0:
            target = smartAddSubTags(r, "{{l.xpath}}")
            target.extend([i.get_et() for i in self.{{l.name}}.values()])
        #{%else%}
        if self.{{l.name}} is not None:
            target = smartAddSubTags(r, "{{l.xpath}}")
            target.append(self.{{l.name}}.get_et())
        #{%endif%}
        #{%endfor%}
        return r

    def clone(self):
        n = copy.copy(self)
        #{%for m in tag.maps%}
        n.{{m.name}} = {}
        for x in self.{{m.name}}.values():
            n.add_{{m.adderName}}(x.clone())
        #{%endfor%}
        #{%for l in tag.lists %}
        n.{{l.name}} = []
        for x in self.{{l.name}}:
            n.add_{{l.adderName}}(x.clone())
        #{%endfor%}
        #{%for s in tag.singletons %}
        if n.{{s.name}} is not None:
            n.{{s.name}} = self.{{s.name}}.clone()
        #{%endfor%}
        return n
        
    #{%for a in tag.attrs.values()%}
    def get_{{a.name}}(self):
        return self.{{a.name}}

    def set_{{a.name}}(self,v):
        self.{{a.name}} = v
    #{%endfor%}

    #{%for l in tag.lists%}
    #{%if not l.suppressAccessors %}
    def add_{{l.adderName}}(self, s):
        self.{{l.name}}.append(s)
        s.parent = self
    #{%else%}
    # {{l.name}} accessor supressed
    #{%endif%}
    #{%endfor%}

    #{%for l in tag.singletons%}
    #{%if not l.suppressAccessors %}
    def set_{{l.adderName}}(self, s):
        if self.{{l.name}} is not None:
            self.{{l.name}}.parent = None
        self.{{l.name}} = s
        self.{{l.name}}.parent = self

    def get_{{l.adderName}}(self):
        return self.{{l.name}}
    #{%else%}
    # {{l.name}} accessor supressed
    #{%endif%}
    #{%endfor%}

    #{%for m in tag.maps%}
    #{%if not m.suppressAccessors %}
    def add_{{m.adderName}}(self, s):
        self.{{m.name}}[s.name] = s
        s.parent = self

    def get_{{m.adderName}}(self, name):
        return self.{{m.name}}[name]

    def get_{{m.name}}(self):
        return self.{{m.name}}
    #{%else%}
    # {{m.name}} accessor supressed
    #{%endif%}
    #{%endfor%}

    def get_children(self):
        r = []

        #{%for l in tag.lists%}
        r = r + self.{{l.name}}
        #{%endfor%}

        #{%for m in tag.maps%}
        r = r + self.{{m.name}}.values()
        #{%endfor%}
        return r

    def dump(self, indent=""):
        print indent + str(self.__class__.__name__)
        for c in self.get_children():
            c.dump(indent + "   ")

classMap["{{tag.tag}}"] = {{classname}}
         
#{% endfor %}


class Part (Base_Part):
    def __init__(self,
                 name=None,
                 deviceset=None,
                 value=None,
                 library=None,
                 device=None,
                 technology=None,
                 attributes=None,
                 variants=None,
             ):
        Base_Part.__init__(self,
                           name,
                           deviceset,
                           value,
                           library,
                           device,
                           technology,
                           attributes,
                           variants)

    # def is_child(self, f):
    #     if f == "schematic":
    #         return False
    #     else:
    #         return EagleFilePart.is_child(self,f)

    def check_sanity(self):
        #assert self.get_device() is not None

        try:
            assert self.find_library() is not None
        except Exception as e:
            raise HighEagleError("Library '" + self.library +  "' missing for " + str(self.name))

        try:
            assert self.find_deviceset() is not None
        except Exception as e:
            raise HighEagleError("DeviceSet '" + self.find_library().name + ":" + self.deviceset + "' missing for " + str(self.name))

        try:
            assert self.find_device() is not None
        except Exception as e:
            raise HighEagleError("Device '" + self.find_library().name + ":" + self.find_deviceset().name + ":" + self.device + "' missing for " + str(self.name))
        
        EagleFilePart.check_sanity(self)
        
         
    def find_library(self):
        """
        Get the library that contains this part
        """
        lib = self.get_root().libraries.get(self.library)
        return lib

    def find_deviceset(self):
        """
        Get the deviceset for this part.
        """
        lib = self.find_library();
        deviceset = lib.devicesets.get(self.deviceset)
        return deviceset
        
    def find_device(self):
        """
        Get the library entry for this part
        """
        deviceset = self.find_deviceset()
        device = deviceset.devices.get(self.device)
        return device

    def find_technology(self):
        """
        Get the library entry for this part
        """
        device = self.find_device()
        tech = device.technologies.get(self.technology)
        return tech

    def set_device(self, library=None, deviceset=None, device=None):
        if library is not None:
            self.library = library
        if deviceset is not None:
            self.deviceset = deviceset
        if device is not None:
            self.device = device
        
    def get_package(self):
        """
        Get the library entry for this part
        """
        device = self.find_device();
        lib = self.find_library();
        if device.package is not None:
            package = lib.packages.get(device.package);
        else:
            package = None
        return package

    # def get_library_attributes(self):
    #     """
    #     Get attribute values for this part that come from the library.
    #     """
    #     return {k:v for (k,v) in self.attributes.iteritems() if v.from_library}

    def set_attribute(self,name, value):
        if name in self.attributes:
            self.attributes[name].value = value
        else:
            n = Attribute(name=name, value=value, in_library=False)
            self.add_attribute(n)

    # def get_attribute(self,name):
    #     return self.attributes.get(name).value

    # def remove_attribute(self,name):
    #     self.attributes[name].parent = None
    #     del self.attributes[name]

classMap["part"] = Part


class Attribute (Base_Attribute):
    """
    EAGLE Attribute section.
    This defines the attributes of an EAGLE Technology section.
    There is also an attributes section in the Schematic section but I've never seen this have anything in there.
    """
    def __init__(self,
                 layer=None,
                 ratio=None,
                 name=None,
                 value=None,
                 y=None,
                 x=None,
                 constant=None,
                 font=None,
                 rot=None,
                 display=None,
                 size=None,
                 in_library=True
                ):
        Base_Attribute.__init__(self,
                                layer,
                                ratio,
                                name,
                                value,
                                y,
                                x,
                                constant,
                                font,
                                rot,
                                display,
                                size)
        self.in_library = False


    def __str__(self):
        return self.name + " = '" + self.value + "' [const=" + str(self.constant) + ";lib=" + str(self.from_library) +"]";

    @classmethod
    def from_et (cls, attribute_root, parent=None):
        n = Base_Attribute.from_et(attribute_root, parent)
        
        if attribute_root.getparent().tag == "technology":
            from_library = True;
        elif attribute_root.getparent().tag == "part":
            from_library = False
        else:
            assert False


        n.in_library = from_library
        return n
        
    def get_et (self):
        n = Base_Attribute.get_et(self)
        
        if not self.in_library:
            if "constant" in n.attrib:
                del n.attrib["constant"]

        return n

classMap["attribute"] = Attribute
