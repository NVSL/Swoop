"""
This module's goal is to provide a python class-structured implementation of the EAGLE PCB file format.
All information in the schematic file is available as class attributes. 
Larger sections are available as classes.
List of sections with a name attribute are implemented as dicts, indexed on the sections name attribute.

The implementation is currently focused on the .sch circuit schematic file formate.
"""

from lxml import etree as ET
import EagleUtil
import copy
import eagleDTD
import StringIO
import types
import operator
import os
import logging as log

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
        assert isinstance(self, EagleFilePart)
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
            #print self
            #print self.get_parent()
            return self.get_parent().get_root()
        else:
            return self

    def clone(self):
        """
        Clone the EagleFilePart.  It should be identical to the orginial, except that the parent should be None
        """
        raise NotImplementedError()

    def _clone(self):
        """
        Simple clone for EagleFileParts with no collections in them.
        """
        n = copy.copy(self)
        n.parent = None
        return n

    def is_child(self, f):
        if f == "parent":
            return False
        else:
            return True
        
    def get_children(self):
        """
        Return all the children of this part as a single iterable.  This general implementation assumes that no file parts hold references to any file parts that are not their children.
        """
        children = []
        for q in self.__dict__:
            if self.is_child(q):
                p = self.__dict__[q]

                #print "+"
                if type(p) is types.ListType:
                    #print "list"
                    #print q
                    children = children + [i for i in p if isinstance(i,EagleFilePart)]
                    #print str(children)
                elif type(p) is types.DictType:
                    #print "dict"
                    #print q
                    children = children + [i for i in p.values() if isinstance(i,EagleFilePart)]
                    #print str(children)
                elif isinstance(p,EagleFilePart):
                    #print q
                    #print "part"
                    children.append(p)
                    #print str(children)

        return children

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

class EagleFile(EagleFilePart):

    DTD = ET.DTD(StringIO.StringIO(eagleDTD.DTD))

    def __init__ (self):
        EagleFilePart.__init__(self)
        self.settings = {}
        self.grid = {}
        self.layersByName = {}
        self.layersByNumber = {}
        self.filename= None

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
            ef = Schematic.from_et(root)
        elif filename[-4:] == ".brd":
            ef = Board.from_et(root)
        elif filename[-4:] == ".lbr":
            ef = LibraryFile.from_et(root,filename=filename)
        else:
            raise HighEagleError("Unknown file suffix: '" + filename[-4:] + "'")
        ef.filename = filename
        ef.check_sanity()
        return ef

    @staticmethod
    def from_et(et,FileType):
        """
        Loads a the common sections of an EagleFile.
        """
        ef = FileType()
        ef.tree = ET.ElementTree(et)
    
        # get sections
        settings = EagleUtil.get_settings(et)
        grid = EagleUtil.get_grid(et)
        layers = EagleUtil.get_layers(et)
        
        #print "Working on settings.", "Found", len(settings)
        for setting in settings:
            for key in setting.attrib:
                ef.settings[key] = setting.attrib[key]
                #print "Got:", key, setting.attrib[key]
                
        for key in grid.attrib:
            ef.grid[key] = grid.attrib[key]

        for layer in layers:
            new_layer = Layer.from_et(layer)
            ef.add_layer(new_layer)

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
        self.layersByNumber[int(layer.number)] = layer
        self.layersByName[layer.name] = layer
        layer.parent = self
        
    def get_layers(self):
        return self.layersByName

    def get_layersByNumber(self):
        return self.layersByNumber

    def get_flippedLayer(self, l):
        if (isinstance(l, str)):
            origName = l
            if l[0] == "t":
                l = "b" + l[1:]
            elif l[0] == "b":
                l = "t" + l[1:]
            elif l == "Top":
                l = "Bottom"
            elif l == "Bottom":
                l = "Top"
            if l not in self.layersByName:
                raise HighEagleError("Tried to flip layer '" + origName + "', but '" + l + "' doesn't exist")
            return name
        elif (isinstance(l,int)):
            if l in self.layersByNumber:
                return self.get_flippedLayer(self, self.layersByNumber[l]).number
            else:
                raise HighEagleError("Can't find layer number " + number)
        elif (isinstance(l,Layer)):
            if l.name in self.layersByName:
                return self.layersByName[get_flippedLayer(l.name)]
            else:
                raise HighEagleError("Can't find layer '" + l.name +"' in this file")

    def layerNumberToName(self, num):
        assert type(num) is int
        if num not in self.layersByNumber:
            raise HighEagleError("No layer number " + str(num))
        return self.layersByNumber[num].name

    def layerNameToNumber(self, name):
        assert type(name) is str
        if name not in self.layersByName:
            raise HighEagleError("No layer named '" + name + "' in " + self.filename)
        return self.layersByName[name].number

    def remove_layer(self, layer):
        if type(layer) is str:
            l = self.layersByName[layer]
            self.remove_layer(l)
        elif type(layer) is int:
            l = self.layersByNumber[layer]
            self.remove_layer(l)
        elif isinstance(layer, Layer):
            self.layersByName[layer.name].parent = None
            del self.layersByName[layer.name]
            del self.layersByNumber[layer.number]
        else:
            raise HighEagleError("Invalid layer spec: " + str(layer))
            
    def get_manifest(self):
        raise NotImplementedError("Manifest for " + str(type(self)))

    def get_library(self, l):
        return self.libraries.get(l)

class EagleDesignFile(EagleFile):
    """
    Super class for sch and brd files to factor out common elements.
    """
    def __init__(self):
        EagleFile.__init__(self)
        self.tree = None
        self.root = None
        self.libraries = {}
        self.attributes = {}
        self.variantdefs = {}
        self.classes = {}

    @staticmethod
    def from_et(et, FileType):

        edf = EagleFile.from_et(et,FileType)
     #   assert len(edf.get_layers()) > 0, "No layers in edfematic."
        libraries = EagleUtil.get_libraries(et)
        attributes = EagleUtil.get_attributes(et)
        variantdefs = EagleUtil.get_variantdefs(et)
        classes = EagleUtil.get_classes(et)
        
        for library in libraries:
            #print library
            new_lib = Library.from_et(library) 
            edf.add_library(new_lib)
            
        for attribute in attributes:
            a = Attribute.from_et(attribute)
            edf.add_attribute(a)
            
        for variantdef in variantdefs:
            raise NotImplementedError("Sheet variant support not implemented")
            
        for net_class in classes:
            #print net_class
            new_class = NetClass.from_et(net_class)
            edf.add_class(new_class)

        return edf
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        
        eagle = EagleUtil.make_eagle()
        #<!ELEMENT schematic (description?, libraries?, attributes?, variantdefs?, classes?, modules?, parts?, sheets?, errors?)>
        #<!ELEMENT board (description?, plain?, libraries?, attributes?, variantdefs?, classes?, designrules?, autorouter?, elements?, signals?, errors?)>

        EagleUtil.set_settings(eagle, self.settings)
        EagleUtil.set_grid(eagle)
        
        for layer in sorted(self.get_layers().values(), key=operator.attrgetter("number")):
            #print layer.name +  " " + str(layer.number)
            EagleUtil.add_layer(eagle, layer.get_et())

        for library in self.libraries.values():
            EagleUtil.add_library(eagle, library.get_et())
            
        for attribute in self.attributes:
            EagleUtil.add_attibute(eagle, attribute.get_et())
            
        for varientdef in self.variantdefs:
            pass
            
        #ET.dump(eagle) 
            
        #print
        #print "Adding net classes"
        
        for net_class in self.classes.values():
            EagleUtil.add_class(eagle, net_class.get_et())
            
        #ET.dump(eagle) 
        
        #print
        #print "Adding parts"
        return eagle

    def add_class (self, c):
        """
        Adds a part to the schematic.
        All gates are placed on the given sheet (default sheet 0).
        """
        self.classes[c.name] = c
        c.parent = self

    def add_attibute(self,a):
        self.attribute[a.name] = a
        a.parent = self
        
    def get_libraries(self):
        return libraries


class Schematic (EagleDesignFile):
    """
    This is the top level for a circuit file.
    
    It contains libraries, parts, sheets, and some other information required by the EAGLE file format.
    """
    def __init__ (self):
        """
        Initialized an empty schematic or loads a schematic from a .sch file if
        a file name is specified.  The empty schematic should be compatible
        with EAGLE and should open and close with no warnings or errors.
        """
        EagleDesignFile.__init__(self)
        self.parts = {}
        self.sheets = []

        
    @staticmethod
    def from_et (et):
        """
        Loads a Schematic from an ElementTree.Element representation.
        """
        sch = EagleDesignFile.from_et(et, Schematic)
        
        parts = EagleUtil.get_parts(et)
        sheets = EagleUtil.get_sheets(et)

        for part in parts:
            #print part
            new_part = Part.from_et(part, schematic=sch)
            sch.add_part(new_part)
            
        #assert len(sch.parts) > 0
            
        for sheet in sheets:
            #print sheet
            new_sheet = Sheet.from_et(sheet)
            sch.add_sheet(new_sheet)
        
        return sch

    @staticmethod
    def from_file (filename):
        return EagleFile.from_file_by_type(filename, Schematic)

    def get_manifest(self, indent=""):
        r = indent + "Libraries (" + str(len(self.libraries)) + ")\n"+ indent
        for l in self.libraries:
            r = r + "\t" + l+ "\n"
            r = r + self.libraries[l].get_manifest(indent + "\t"  + "\t") + "\n"+indent
        r = r + "Parts (" + str(len(self.parts)) + ")\n"+ indent
        for l in self.parts:
            r = r + "\t" + l + "\n"+ indent
        r = r + "Sheets (" + str(len(self.sheets)) + ")\n"+ indent
        return r
        
    def add_part (self, p, sheet_index=0):
        """
        Adds a part to the schematic.
        All gates are placed on the given sheet (default sheet 0).
        """
        self.parts[p.name] = p
        p.parent = self
        # add part to schematic
        # add part to sheet_index
        # make sure part is in library
        
        
    def add_sheet(self, s):
        """
        Add a sheet to the schematic.
        """
        self.sheets.append(s)
        s.parent = self
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        
        eagle = EagleDesignFile.get_et(self)
        
        for part in self.parts.values():
            EagleUtil.add_part(eagle, part.get_et())

        #print "Adding sheets"
        for i, sheet in enumerate(self.sheets):
            EagleUtil.add_sheet(eagle, sheet.get_et())
            #print "Sheet", i
            #ET.dump(eagle) 

#        if len(self.sheets) == 0:
#            EagleUtil.add_sheet(eagle, EagleUtil.make_empty_sheet())
            
        #ET.dump(eagle)    
            
        return eagle

    def get_parts(self):
        return self.parts
    
    def add_library(self, library):
        self.libraries[library.name] = library
        library.parent = self

        
class Board (EagleDesignFile):
    """
    This is the top level for a board file.
    """
    def __init__ (self):
        """
        Initialized an empty board.
        """
        EagleDesignFile.__init__(self)

        self.plain = []
        self.designrules = {}
        self.autorouter_passes = {}
        self.elements = {}
        self.signals = {}
        
    @staticmethod
    def from_et (et):
        """
        Loads a Schematic from an ElementTree.Element representation.
        """

        brd = EagleDesignFile.from_et(et,Board)

        # get sections
        plain = EagleUtil.get_plain(et)
        designrules = EagleUtil.get_designrules(et)
        autorouter = EagleUtil.get_autorouter_passes(et)
        elements = EagleUtil.get_elements(et)
        signals = EagleUtil.get_signals(et)
        
        for d in designrules:
            log.info("Added param")
            d = DesignRules.from_et(d)
            brd.add_designrules(d)
            
        for p in autorouter:
            log.info("Autorouter pass")
            new_pass= Pass.from_et(p)
            brd.add_autorouter_pass(new_pass)
            
        for element in elements:
            log.info("Added element")
            new_element = Element.from_et(element)
            brd.add_element(new_element)
        
        for signal in signals:
            log.info("Added signals")
            new_signal = Signal.from_et(signal)
            brd.add_signal(new_signal)
        
        for w in plain:
            log.info("Added plain")
            n = DrawingElement.from_et(w)
            brd.add_plain_element(n)
        
        return brd
    
    @staticmethod
    def from_file (filename):
        return EagleFile.from_file_by_type(filename, Board)

    def get_et(self):
        """
        Returns the ElementTree.Element xml representation.
        """

        eagle = EagleDesignFile.get_et(self)
        
        for e in self.elements.values():
            print "1"
            EagleUtil.add_element(eagle, e.get_et())
        for e in self.plain:
            print "2"
            EagleUtil.add_plain_element(eagle, e.get_et())
        for s in self.signals.values():
            print "3"
            EagleUtil.add_signal(eagle, s.get_et())
        for s in self.autorouter_passes.values():
            print "4"
            EagleUtil.add_autorouter_pass(eagle, s.get_et())
            
                
            
        return eagle

    def add_designrules(self,d):
        self.designrules[d.name] = d
        d.parent = self

    def add_plain_element(self,d):
        self.plain.append(d)
        d.parent = self
    
    def add_autorouter_pass(self,a):
        self.autorouter_passes[a.name] = a
        a.parent = self
        
    def add_element(self,e):
        self.elements[e.name] = e
        e.parent = self

    def add_signal(self,s):
        self.designrules[s.name] = s
        s.parent = self

class DesignRules(EagleFilePart):
    def __init__(self, name=None):
        EagleFilePart.__init__(self)
        self.name = name
        self.params ={}
        self.descriptions = []
        
    @staticmethod
    def from_et(et):
        dr = DesignRules(name=et.get("name"))

        params = EagleUtil.get_params(et)
        descriptions = EagleUtil.get_descriptions(et)
                
        for param in params:
            new_param = Param.from_et(param)
            dr.add_param(new_param)

        for d in descriptions:
            d = Description.from_et(d)
            dr.add_description(d)
        return dr
        
    def add_param(self,e):
        self.params[e.name] = e
        e.parent = self

    def add_description(self,s):
        self.descriptions.append(s)
        s.parent = self

class AutorouterPass(EagleFilePart):
    def __init__(self, name=None):
        EagleFilePart.__init__(self)
        self.name = name
        self.params ={}
        
    @staticmethod
    def from_et(et):
        dr = AutorouterPass(et.get("name"))

        params = EagleUtil.get_params(et)
                
        for param in params:
            new_param = Param.from_et(param)
            brd.add_designrules(new_param)

    def add_param(self,e):
        self.params[e.name] = e
        e.parent = self

class Element(EagleFilePart):
    def __init__(self, name=None,library=None,package=None,value=None,x=None,y=None,attributes=None):
        EagleFilePart.__init__(self)
        self.name = name
        self.library = library
        self.package = package
        self.value= value
        self.x = x
        self.y = y
        if attributes in None:
            self.attributes ={}
        else:
            self.attributes = attributes
        
    @staticmethod
    def from_et(et):
        e = Element(
                     name=et.get("name"),
                     library=et.get("library"),
                     package=et.get("package"),
                     value=et.get("value"),
                     x=et.get("x"),
                     y=et.get("y"))
        
        attrs = EagleUtil.get_attributes(et)
                
        for a in attrs:
            n = Attribute.from_et(a)
            e.add_attribute(n)

    def add_attribute(self,e):
        self.attributes[e.name] = e
        e.parent = self


class Pin (EagleFilePart):
    """
    EAGLE pin tag.
    This is a connectible pin on a circuit Symbol. It maps to a Pad or SMD on a Package.
    """
    
    def __init__ (self, name=None, x=None, y=None, visible=None, length=None, direction=None, swaplevel=None, rot=None):
        EagleFilePart.__init__(self)
        assert name is not None
        self.name = name
        self.x = x
        self.y = y
        self.visible = visible
        self.length = length
        self.direction = direction
        self.swaplevel = swaplevel
        self.rot = rot

    def clone(self):
        return self._clone()
    
    @classmethod
    def from_et (cls, pin_root):
        return cls(
            name=pin_root.get("name"),
            x=pin_root.get("x"),
            y=pin_root.get("y"),
            visible=pin_root.get("visible"),
            length=pin_root.get("length"),
            direction=pin_root.get("direction"),
            swaplevel=pin_root.get("swaplevel"),
            rot=pin_root.get("rot")
        )
        
    def get_et (self):
        return EagleUtil.make_pin(
            name=self.name,
            x=self.x,
            y=self.y,
            visible=self.visible,
            length=self.length,
            direction=self.direction,
            swaplevel=self.swaplevel,
            rot=self.rot
        )
      
class LibraryFile(EagleFile):
  
    def __init__ (self):
        """
        Initialized an empty schematic or loads a schematic from a .sch file if
        a file name is specified.  The empty schematic should be compatible
        with EAGLE and should open and close with no warnings or errors.
        """
        EagleFile.__init__(self)
        self.name = None
        self.libraries = None

        #for layer in Layer.default_layers():
        #    self.add_layer(layer)
        


    @staticmethod
    def from_file (filename):
        return EagleFile.from_file_by_type(filename, LibraryFile)

    @staticmethod
    def from_et (et, filename=None):
        """
        Loads a Library file from an ElementTree.Element representation.
        """
        lbr = EagleFile.from_et(et,LibraryFile)
        
        # get sections
        library = EagleUtil.get_library(et)
        
        lbr.library = Library.from_et(library)
        lbr.library.parent = lbr
        if lbr.library.name is None:
            lbr.library.name = os.path.basename(filename)[:-4]

        return lbr

    def write (self, filename):
        """
        Exports the Schematic to an EAGLE schematic file.
        
        """
        self.library.name = os.path.basename(filename)[:-4]
        EagleFile.write(self,filename)
            
    def get_library(self):
        return self.library
    
    def get_manifest(self, indent=""):
        return self.library.get_manifest(indent + "\t")

    def get_et (self):
        """
        Returns the ElementTree.Element xml representation of the library file
        """
        
        eagle = EagleUtil.make_eagle()
        EagleUtil.set_settings(eagle, self.settings)
        EagleUtil.set_grid(eagle)

        for layer in sorted(self.get_layers().values(), key=operator.attrgetter("number")):
            #print layer.name +  " " + str(layer.number)
            EagleUtil.add_layer(eagle, layer.get_et())

        EagleUtil.add_library_to_library_file(eagle, self.library.get_et())
            
        return eagle


    def get_library_copy(self):
        return copy.deepcopy(self.library)
        
class Library (EagleFilePart):
    def __init__ (self, name=None, description="", packages=None, symbols=None, devicesets=None):        
        EagleFilePart.__init__(self)
        self.name = name
        if packages is None: packages = {}
        if symbols is None: symbols = {}
        if devicesets is None: devicesets = {}
        
        self.description = description
        self.packages = packages
        self.symbols = symbols
        self.devicesets = devicesets

    def clone(self):
        n = self._clone()
        
        for p in self.packages.values():
            n.add_package(p.clone())

        for s in self.symbols.values():
            n.add_symbol(s.clone())

        for ds in self.devicesets.values():
            n.add_deviceset(ds.clone())

        return n;
        
    @classmethod
    def from_et (cls,library_root):
        assert library_root.tag == "library"
        lib = cls( name=library_root.get("name"))
        #print "Loading library:", lib.name
        lib.description = EagleUtil.get_description(library_root)
        
        packages = EagleUtil.get_packages(library_root)
        symbols = EagleUtil.get_symbols(library_root)
        devicesets = EagleUtil.get_devicesets(library_root)
        
        lib.packages = {}
        for package in packages:
            new_package = Package.from_et(package)
            assert new_package.name not in lib.packages, "Cannot have duplicate package names: "+new_package.name
            lib.add_package(new_package)
            
        lib.symbols = {}
        for symbol in symbols:
            new_symbol = Symbol.from_et(symbol)
            assert new_symbol.name not in lib.symbols, "Cannot have duplicate symbol names: "+new_symbol.name
            lib.add_symbol(new_symbol)
            
        lib.devicesets = {}
        for deviceset in devicesets:
            new_deviceset = DeviceSet.from_et(deviceset)
            assert new_deviceset.name not in lib.devicesets, "Cannot have duplicate devicesets names: "+new_deviceset.name
            lib.add_deviceset(new_deviceset)
            
            
        assert lib is not None
        return lib

    def get_manifest(self, indent=""):
        r = indent + "Symbols (" + str(len(self.symbols)) + ")\n"+ indent
        for l in self.symbols:
            r = r + "\t" + l+ "\n" + indent
        r = r + "Packages (" + str(len(self.packages)) + ")\n"+ indent
        for l in self.packages:
            r = r + "\t" + l + "\n"+ indent
        r = r + "DeviceSets (" + str(len(self.devicesets)) + ")\n"+ indent
        for l in self.devicesets:
            r = r + "\t" + l + "\n"+ indent
        return r
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        return EagleUtil.make_library(
            name=self.name,
            packages=[package.get_et() for package in self.packages.values()],
            symbols=[symbol.get_et() for symbol in self.symbols.values()],
            devicesets=[deviceset.get_et() for deviceset in self.devicesets.values()],
            description=self.description
        )
        
    def get_part (self, name=None, deviceset=None, device=None, package=None):
        """
        Searches the library for a device that fits the specified parameters.
        """

    def get_deviceset(self, name):
        return self.devicesets.get(name)

    def get_symbol(self, name):
        return self.symbols.get(name)

    def get_package(self, name):
        return self.packages.get(name)

    def remove_deviceset(self, deviceset):
        if type(deviceset) == str:
            name = deviceset
        elif type(deviceset) == DeviceSet:
            name = deviceset.name
            deviceset.parent = None
        else:
            raise HighEagleError("Wrong type of argument to remove_deviceset()")

        if name not in self.devicesets:
            raise HighEagleError("Deviceset '" + name +"' is not in library '" + self.name + "'")
        del self.devicesets[name]

    def remove_symbol(self, symbol):
        if type(symbol) == str:
            name = symbol
        elif type(symbol) == Symbol:
            name = symbol.name
            symbol.parent = None
        else:
            raise HighEagleError("Wrong type of argument to remove_symbol()")

        if name not in self.symbols:
            raise HighEagleError("Symbol '" + name +"' is not in library '" + self.name + "'")
        del self.symbols[name]

    def remove_package(self, package):
        if type(package) == str:
            name = package
        elif type(package) == Package:
            name = package.name
            package.parent = None
        else:
            raise HighEagleError("Wrong type of argument to remove_package()")

        if name not in self.packages:
            raise HighEagleError("Package '" + name +"' is not in library '" + self.name + "'")
        del self.packages[name]

        
    def add_deviceset(self, deviceset):
        assert type(deviceset) is DeviceSet
        self.devicesets[deviceset.name] = deviceset
        deviceset.parent = self

    def add_package(self, package):
        assert type(package) is Package
        self.packages[package.name] = package
        package.parent = self

    def add_symbol(self, symbol):
        assert type(symbol) is Symbol
        self.symbols[symbol.name] = symbol
        symbol.parent = self

class Package (EagleFilePart):
    def __init__ (self, name=None, contacts=None, drawingElements=None):        
        EagleFilePart.__init__(self)
        self.name = name
        
        if contacts is None: contacts = {}
        if drawingElements is None: drawingElements = []
        
        self.drawingElements = drawingElements
        self.contacts = contacts
        
    def __str__ (self):
        string = ""
        for key in self.__dict__:
            string += key+": "+(self.__dict__[key].__str__())+"\n"
        return string
        
    def clone(self):
        n = self._clone()
        n.drawingElements = []
        for i in self.drawingElements:
            n.add_drawingElement(i.clone())
        for i in self.contacts.values():
            n.add_contact(i.clone())
        return n

    @staticmethod
    def from_et (package_root):
        new_package = Package()
        new_package.name = None
        new_package.contacts = {}
        new_package.drawingElement = []
        
        new_package.name = package_root.get("name")
        pads = EagleUtil.get_pads(package_root)
        smds = EagleUtil.get_smds(package_root)
        drawingElements = EagleUtil.get_drawingElements(package_root)
        
        for pad in pads:
            new_pad = Pad.from_et(pad)
            assert new_pad.name not in new_package.contacts, "Cannot add pad with duplicate name: "+new_pad.name
            new_package.add_contact(new_pad)
        
        for smd in smds:
            new_smd = SMD.from_et(smd)
            assert new_smd.name not in new_package.contacts, "Cannot add smd with duplicate name: "+new_smd.name
            new_package.add_contact(new_smd)
            
        for drawingElement in drawingElements:
            new_drawingElement = DrawingElement.from_et(drawingElement)
            new_package.add_drawingElement(new_drawingElement)

        return new_package
        
    def get_et (self):
        #assert len(self.drawingElements) > 0, self.name # not really needed I guess, might just be pads for the package
        return EagleUtil.make_package(
            name=self.name, 
            drawingElements=[drawingElement.get_et() for drawingElement in self.drawingElements], 
            contacts=[contact.get_et() for contact in self.contacts.values()]
        )
    
    def add_drawingElement(self,e):
        self.drawingElements.append(e)
        e.parent = self

    def add_contact(self,p):
        self.contacts[p.name] = p
        p.parent = self


class Pad (EagleFilePart):
    """
    EAGLE pad tag.
    This is a through-hole contact in a Package that gets mapped to a Pin on a Gate.
    """
  
    def __init__ (self, name=None, x=None, y=None, drill=None, diameter=None, shape=None, rot=None):        
        EagleFilePart.__init__(self)
        self.name = name
        self.x = x
        self.y = y
        self.drill = drill
        self.diameter = diameter
        self.shape = shape
        self.rot = rot

    def clone(self):
        return self._clone()

    @staticmethod
    def from_et (pad_root):
        assert pad_root.tag == "pad"
        return Pad(
            name=pad_root.get("name"),
            x=pad_root.get("x"),
            y=pad_root.get("y"),
            drill=pad_root.get("drill"),
            diameter=pad_root.get("diameter"),
            shape=pad_root.get("shape"),
            rot=pad_root.get("rot")
        )
        
    def get_et (self):
        return EagleUtil.make_pad(
            name=self.name,
            x=self.x,
            y=self.y,
            drill=self.drill,
            diameter=self.diameter,
            shape=self.shape,
            rot=self.rot
        )

class DrawingElement (EagleFilePart):
    """
    EAGLE drawing tag.
    This is an abstract tag that is used for wire, rectangle, circle, etc.
    """
    
    def __init__(self,
                 layer=None):
        EagleFilePart.__init__(self)
        # ef = self.get_file()
        # assert ef is not None

        # if type(layer) is int:
        #     assert layer in ef.layersByNumber
        #     self.layer = ef.layersByNumber[layer].name
        # elif type(layer) is str:
        #     assert layer in ef.layersByName
        #     self.layer = layer
        self.layer = layer
                
    def clone(self):
        return self._clone()

    @staticmethod
    def from_et (drawing_root):
        if drawing_root.tag == "polygon":
            return Polygon.from_et(drawing_root)
        elif drawing_root.tag == "wire":
            return Wire.from_et(drawing_root)
        elif drawing_root.tag == "text":
            return Text.from_et(drawing_root)
        elif drawing_root.tag == "dimension":
            raise NotImplementedError("Tag '" + drawing_root.tag + "' not yet supported")
            return Dimension.from_et(drawing_root)
        elif drawing_root.tag == "circle":
            return Circle.from_et(drawing_root)
        elif drawing_root.tag == "rectangle":
            return Rectangle.from_et(drawing_root)
        elif drawing_root.tag == "frame":
            raise NotImplementedError("Tag '" + drawing_root.tag + "' not yet supported")
            return Frame.from_et(drawing_root)
        elif drawing_root.tag == "hole":
            raise NotImplementedError("Tag '" + drawing_root.tag + "' not yet supported")
            return Hole.from_et(drawing_root)
        else:
            raise Exception("Don't know how to parse "+drawing_root.tag+" tag as a drawing tag.")        

class Rectangle (DrawingElement):
    """
    EAGLE rectangle tag.
    This is used to draw text on the schematic or board.
    """
    def __init__ (
        self, 
        x1=None, 
        y1=None, 
        x2=None, 
        y2=None,
        layer=None, 
    ):
        DrawingElement.__init__(self, layer)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        
    @staticmethod
    def from_et (rectangle_root):
        assert rectangle_root.tag == "rectangle"
        return Rectangle(
            x1=rectangle_root.get("x1"),
            y1=rectangle_root.get("y1"),
            x2=rectangle_root.get("x2"),
            y2=rectangle_root.get("y2"),
            layer=rectangle_root.get("layer")
        )
        
    def get_et (self):
        return EagleUtil.make_rectangle(
            x1=self.x1,
            x2=self.x2,
            y1=self.y1,
            y2=self.y2,
            layer=self.layer
        )
        
class Text (DrawingElement):
    """
    EAGLE text tag.
    This is used to draw text on the schematic or board.
    """
    def __init__ (self, x=None, y=None, size=None, layer=None, text=None):        
        DrawingElement.__init__(self,layer)
        self.x = x
        self.y = y
        self.size = size
        self.text = text

    @staticmethod
    def from_et (text_root):
        assert text_root.tag == "text"
        return Text(
            x=text_root.get("x"),
            y=text_root.get("y"),
            size=text_root.get("size"),
            layer=text_root.get("layer"),
            text=text_root.text
        )
        
    def get_et (self):
        return EagleUtil.make_text(
            x=self.x,
            y=self.y,
            size=self.size,
            layer=self.layer,
            text=self.text
        )
        
class Circle (DrawingElement):
    """
    EAGLE circle tag.
    This is used to draw a circle on the schematic or board.
    """
    def __init__ (self, x=None, y=None, radius=None, width=None, layer=None):
        DrawingElement.__init__(self,layer)
        self.x = x
        self.y = y
        self.radius = radius
        self.width = width

    @staticmethod
    def from_et (circle_root):
        assert circle_root.tag == "circle"
        return Circle(
            x=circle_root.get("x"),
            y=circle_root.get("y"),
            radius=circle_root.get("radius"),
            width=circle_root.get("width"),
            layer=circle_root.get("layer"))
        
    def get_et (self):
        return EagleUtil.make_circle(
            x=self.x,
            y=self.y,
            radius=self.radius,
            width=self.width,
            layer=self.layer
        )
        

        
class SMD (EagleFilePart):
    """
    EAGLE smd tag.
    This is a smd contact in a Package that gets mapped to a Pin on a Gate.
    """
  
    def __init__ (self, name=None, x=None, y=None, dx=None, dy=None, layer=None, rot=None):
        EagleFilePart.__init__(self)
        self.name = name
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.layer = layer
        self.rot = rot
    
    def clone(self):
        return self._clone()
    
    @staticmethod
    def from_et (smd_root):
        assert smd_root.tag == "smd"
        return SMD(
            name=smd_root.get("name"),
            x=smd_root.get("x"),
            y=smd_root.get("y"),
            dx=smd_root.get("dx"),
            dy=smd_root.get("dy"),
            layer=smd_root.get("layer"),
            rot=smd_root.get("rot")
        )        
        
    def get_et (self):
        return EagleUtil.make_SMD(
            name=self.name,
            x=self.x,
            y=self.y,
            dx=self.dx,
            dy=self.dy,
            layer=self.layer,           
            rot=self.rot
        )
               
class Symbol (EagleFilePart):
    """
    EAGLE symbol section.
    This section holds circuit diagram symbols that can be used as gates for Devices and Parts.
    """
    
    def __init__ (self, name=None, drawingElements=None, pins=None):
        EagleFilePart.__init__(self)
        self.name = name
        
        if drawingElements is None: 
            drawingElements = []
        if pins is None: pins = {}
        
        self.drawingElements = drawingElements
        self.pins = pins
    
    def clone(self):
        n = self._clone()
        n.drawingElements = []
        for i in self.drawingElements:
            n.add_drawingElement(i.clone())
        for i in self.pins.values():
            n.add_pin(i.clone())
        return n

    def add_drawingElement(self,e):
        self.drawingElements.append(e)
        e.parent = self

    def add_pin(self,p):
        self.pins[p.name] = p
        p.parent = self

    @classmethod
    def from_et (cls, symbol_root):
        assert symbol_root.tag == "symbol"
        
        symbol = cls()
        symbol.name = symbol_root.get("name")
        
        drawingElements = EagleUtil.get_drawingElements(symbol_root)
        for drawing in drawingElements:
            symbol.add_drawingElement(DrawingElement.from_et(drawing))
            
        pins = EagleUtil.get_pins(symbol_root)
        for pin in pins:
            symbol.add_pin(Pin.from_et(pin))

        return symbol

    def get_et (self):
        return EagleUtil.make_symbol(
            name=self.name,
            drawingElements=[drawing.get_et() for drawing in self.drawingElements],
            pins=[pin.get_et() for pin in self.pins.values()]
        )
    
class Part (EagleFilePart):
    def __init__ (self, name=None, library=None, deviceset=None, device=None, package=None, value=None, schematic=None, technology=None):
        EagleFilePart.__init__(self)
        self.name = name
        self.library = library
        self.deviceset = deviceset
        self.device = device
        self.package = package
        self.technology = technology
        self.value = value
        self.schematic = schematic
        self.attributes = {}

    def is_child(self, f):
        if f == "schematic":
            return False
        else:
            return EagleFilePart.is_child(self,f)

    def check_sanity(self):
        #assert self.get_device() is not None

        try:
            assert self.get_library() is not None
        except Exception as e:
            raise HighEagleError("Library '" + self.library +  "' missing for " + str(self.name))

        try:
            assert self.get_deviceset() is not None
        except Exception as e:
            raise HighEagleError("DeviceSet '" + self.get_library().name + ":" + self.deviceset + "' missing for " + str(self.name))

        try:
            assert self.get_device() is not None
        except Exception as e:
            raise HighEagleError("Device '" + self.get_library().name + ":" + self.get_deviceset().name + ":" + self.device + "' missing for " + str(self.name))
        
        EagleFilePart.check_sanity(self)
        
    @staticmethod
    def from_et (root, schematic=None):
        name = root.get("name")
        library = root.get("library")
        deviceset = root.get("deviceset")
        device = root.get("device")
        package = root.get("package")
        value = root.get("value")
        technology =root.get("technology")

        if technology is None:
            technology = ""

        part = Part(
                    name=name, 
                    library=library, 
                    deviceset=deviceset, 
                    device=device, 
                    package=package, 
                    value=value, 
                    schematic=schematic,
                    technology=technology)

        #print "here: "+ str(part.get_device().technologies[""].attributes)

        for a in part.get_technology().attributes.values():
            part.add_attribute(a.clone())

        for i in part.attributes.values():
            i.in_library = False
        
        for i in root.findall("./attribute"):
            if i.get("name") in part.attributes:
                if part.attributes[i.get("name")].constant:
                    raise HighEagleError("Tried to set constant attribute '" 
                                         + i.name + "' on part '" 
                                         + part.name + "'.")
                part.attributes[i.get("name")].value = i.get("value")
            else:
                part.add_attribute(Attribute.from_et(i))
        
        return part
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        libAttrs = self.get_technology().attributes
        attrs = []
        for a in self.attributes.values():
            if a.name not in libAttrs:
                attrs.append(a.get_et())
            elif libAttrs[a.name].constant:
                pass
            elif libAttrs[a.name].value == a.value:
                pass
            else:
                attrs.append(a.get_et())

                #print self.value
        return EagleUtil.make_part(
            name=self.name,
            deviceset=self.deviceset,
            library=self.library,
            device=self.device,
            value=unicode(self.value),
            attributes=attrs
        )
        

    def add_attribute(self,attribute):
        self.attributes[attribute.name] = attribute
        attribute.parent = self
         
    def get_library(self):
        """
        Get the library that contains this part
        """
        #try:
        lib = self.schematic.libraries.get(self.library)
        #except:
        #raise EagleFormatError("Missing library '" + self.library + "' for part '" + self.name + "'.")
        return lib

    def get_deviceset(self):
        """
        Get the deviceset for this part.
        """

        lib = self.get_library();

        #        try:
        deviceset = lib.devicesets.get(self.deviceset)
        #        except:
        #            raise EagleFormatError("Missing device set '" + self.library + ":" + self.deviceset + "' for part '" + self.name + "' in file " +self.get_file().filename +".")
        return deviceset
        
    def get_device(self):
        """
        Get the library entry for this part
        """
        deviceset = self.get_deviceset()

        #        try:
        device = deviceset.devices.get(self.device)
        #except:
        #    raise EagleFormatError("Missing device '" + self.library + ":" + self.deviceset + ":" + self.device  + "' for part '" + self.name + "'.")
        
        return device

    def get_technology(self):
        """
        Get the library entry for this part
        """
        device = self.get_device()

        #try:
        tech = device.technologies.get(self.technology)
        #except:
        #    raise EagleFormatError("Missing technology '" + self.library + ":" + self.deviceset + ":" + self.device  + ":" + self.technology+  "' for part '" + self.name + "'.")
        
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
        device = self.get_device();
        lib = self.get_library();
        #try:
        if device.package is not None:
            package = lib.packages.get(device.package);
        else:
            package = None
        #except:
        #    raise EagleFormatError("Missing package '" + device.package + "' for part '" + self.name + "'.")
        return package
        
    # def get_gates(self):
    #     """
    #     Get the library entry for this part
    #     """
    #     deviceset = self.get_deviceset();
    #     lib = self.get_library();
    #     #print self
    #     #print len(deviceset.gates)
    #     #print deviceset.name
    #     assert len(deviceset.gates) == 1
    #     #try:
    #     gate = lib.symbols[deviceset.gates.values()[0].symbol];
    #     #except:
    #     #    raise EagleFormatError("Missing gate '" + deviceset.gate["G$1"] + "' for part '" + self.name + "'.")
    #     return gate
    
    def get_attributes(self):
        """
        Get attribute values for this part.
        """
        return self.attributes

    def get_library_attributes(self):
        """
        Get attribute values for this part that come from the library.
        """
        return {k:v for (k,v) in self.attributes.iteritems() if v.from_library}

    def set_attribute(self,name, value):
        if name in self.attributes:
            self.attributes[name].value = value
        else:
            n = Attribute(name=name, value=value, in_library=False)
            self.add_attribute(n)

    def get_attribute(self,name):
        return self.attributes.get(name).value

    def remove_attribute(self,name):
        self.attributes[name].parent = None
        del self.attributes[name]
    
class DeviceSet (EagleFilePart):
    def __init__ (self, name=None, prefix=None, devices=None, description="", gates=None):
        EagleFilePart.__init__(self)
    
        if devices is None: devices = {}
        if gates is None: gates = {}
    
        self.name = name
        self.prefix = prefix
        self.description = description
        self.gates = gates
        self.devices = devices

    def check_sanity(self):
        assert isinstance(self.parent, Library)
        
        for g in self.gates.values():
            if g.symbol not in self.parent.symbols:
                raise HighEagleError("Symbol '" + g.symbol + "' missing in '" + self.parent.name + ":" + self.name + "'")

        EagleFilePart.check_sanity(self)
        
    @classmethod
    def from_et (cls, deviceset_root):
        deviceset = cls(name=deviceset_root.get("name"))
        deviceset.description = EagleUtil.get_description(deviceset_root)
        
        gates = EagleUtil.get_gates(deviceset_root)
        devices = EagleUtil.get_devices(deviceset_root)
        
        for gate in gates:
            new_gate = Gate.from_et(gate)
            deviceset.add_gate(new_gate)
            
        for device in devices:
            new_device = Device.from_et(device)
            deviceset.add_device(new_device)
        
        return deviceset
        
    def clone(self):
        n = self._clone()
        
        for i in self.gates.values():
            n.add_gate(i.clone())
        for i in self.devices.values():
            n.add_device(i.clone())
        return n

    def add_gate(self, a):
        self.gates[a.name] = a
        a.parent = self

    def add_device(self, a):
        self.devices[a.name] = a
        a.parent = self

    def remove_device(self, d):
        del self.devices[d.name]
        d.parent = None
        
    def get_gates(self):
        return self.gates

    def get_devices(self):
        return self.devices

    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        return EagleUtil.make_deviceset(
            name=self.name,
            prefix=self.prefix,
            description=self.description,
            gates=[gate.get_et() for gate in self.gates.values()],
            devices=[device.get_et() for device in self.devices.values()]
        )

    # This converts the deviceset into an external device.  This means that it
    # has no associated package.  It can, however, have attributes, and those
    # are stored in the "" device.  You can't just delete all the packages,
    # since you'd lose the attributes.  This copies them from the first
    # package.
    def convertToExternal(self):
        if len(self.get_devices()) > 0:
            d = self.get_devices().values()[0]
            for i in self.get_devices().values():
                self.remove_device(i)
            d.name = ""
            d.package = ""
            d.clear_connects()
        else:
            d = Device(self, "",technologies=[Technology(name="")])

        self.add_device(d)
        for t in d.get_technologies().values():
            t.add_attribute(Attribute(t, name="_EXTERNAL_"))

class Gate (EagleFilePart):
    """
    EAGLE Gate.    
    This is a subsection of DeviceSet that specifies the schematic symbol for all Devices in the DeviceSet.
    """
    
    def __init__ (self, name=None, symbol=None, x=0, y=0):
        EagleFilePart.__init__(self)
        self.name = name
        self.symbol = symbol
        self.x = x
        self.y = y
        
    def clone(self):
        return self._clone()

    @staticmethod
    def from_et (gate_root):
        gate = Gate(
            name=gate_root.get("name"),
            symbol=gate_root.get("symbol"),
            x=gate_root.get("x"),
            y=gate_root.get("y")
        )
        return gate
        
    def get_et (self):
        return EagleUtil.make_gate(
            name=self.name,
            symbol=self.symbol,
            x=self.x,
            y=self.y
        )

    def get_library(self):
        l = c.get_parent().get_parent()
        assert isinstance(l, Library)
        return l
                
    def get_symbol(self):
        return self.get_library().symbols[self.symbol]
        
class Connect (EagleFilePart):
    """
    EAGLE connect tag.
    This maps a Gate's Pin to a Package's Pad or SMD. Subsection of Device.
    """
    
    def __init__ (self, gate=None, pin=None, pad=None):
        EagleFilePart.__init__(self)
        self.gate = gate
        self.pin = pin
        self.pad = pad

    def clone(self):
        return self._clone()
        
    @classmethod
    def from_et (cls,connect_root):
        assert connect_root.tag == "connect"
        return cls(
            gate=connect_root.get("gate"),
            pin=connect_root.get("pin"),
            pad=connect_root.get("pad")
        )
        
    def get_et (self):
        return EagleUtil.make_connect(
            gate=self.gate,
            pin=self.pin,
            pad=self.pad
        )
        
class Device (EagleFilePart):
    def __init__ (self, name=None, package=None, connects=None, technologies=None):
        EagleFilePart.__init__(self)
        self.connects = []
        self.technologies = {}
        
        self.name = name
        self.package = package
        if connects is not None: 
            for i in connects:
                self.add_connect(i)
        if technologies is not None:
            for i in technologies:
                self.add_technology(i)

    @classmethod
    def from_et (cls, device_root):
        assert device_root.tag == "device"
        device = cls()
        
        device.name = device_root.get("name")
        device.package = device_root.get("package")
        
        connects = EagleUtil.get_connects(device_root)
        for connect in connects:
            device.add_connect(Connect.from_et(connect))
        
        technologies = EagleUtil.get_technologies(device_root)
        for technology in technologies:
            device.add_technology(Technology.from_et(technology))
                        
        return device
        
    def clone(self):
        n = self._clone()
        
        n.connects = []
        for i in self.connects:
            n.add_connect(i.clone())
        for i in self.technologies.values():
            n.add_technology(i.clone())
        return n

    def add_connect(self, a):
        self.connects.append(a)
        a.parent = self

    def clear_connects(self):
        for c in self.connects:
            c.parent = None
        self.connects=[]
        
    def add_technology(self, a):
        self.technologies[a.name] = a
        a.parent = self
        
    def get_technologies(self):
        return self.technologies

    def get_library(self):
        l = self.get_parent().get_parent()
        assert isinstance(l, Library)
        return l
    
    def get_package(self):
        if self.package is None:
            return None
        else:
            return self.get_library().packages[self.package]
            
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        return EagleUtil.make_device(
            connects=[connect.get_et() for connect in self.connects],
            name=self.name,
            package=self.package,
            technologies=[tech.get_et() for tech in self.technologies.values()]
        )
        
class Technology (EagleFilePart):
    """
    EAGLE Technology section.
    This is a subsection of Device.
    """
    
    def __init__ (self, name=None, attributes=None):
        EagleFilePart.__init__(self)
        if attributes is None: attributes = {}
        self.attributes = attributes
        self.name = name
        
    def clone(self):
        n = self._clone()
        
        for i in self.attributes.values():
            n.add_attribute(i.clone())
        return n

    @classmethod
    def from_et (cls, technology_root):
        tech = cls()
        tech.name = technology_root.get("name")
        attributes = EagleUtil.get_attributes(technology_root)
        
        for attribute in attributes:
            tech.add_attribute(Attribute.from_et(attribute))
 
        return tech
        
    def add_attribute(self, a):
        self.attributes[a.name] = a
        a.parent = self

    def get_et (self):
        attrs = [a.get_et() for a in self.attributes.values()]
        return EagleUtil.make_technology(name=self.name, attributes=attrs)
        
class Attribute (EagleFilePart):
    """
    EAGLE Attribute section.
    This defines the attributes of an EAGLE Technology section.
    There is also an attributes section in the Schematic section but I've never seen this have anything in there.
    """
    
    def __init__ (self, name=None, value=None, constant=None, from_library=False, in_library=True):
        EagleFilePart.__init__(self)
        self.name = name
        self.value = value
        self.constant = constant
        self.from_library = from_library
        self.in_library = in_library

    def __str__(self):
        return self.name + " = '" + self.value + "' [const=" + str(self.constant) + ";lib=" + str(self.from_library) +"]";

    def clone(self):
        return self._clone()

    @staticmethod
    def from_et (attribute_root):
        assert attribute_root.tag == "attribute"
        #ET.dump(attribute_root);
        #ET.dump(attribute_root.getparent());
        if attribute_root.get("extent") is not None:
            raise NotImplementedError("BRD-style Attributes not supported yet")
        if attribute_root.get("x") is not None:
            raise NotImplementedError("BRD-style Attributes not supported yet")
        if attribute_root.get("y") is not None:
            raise NotImplementedError("BRD-style Attributes not supported yet")
        if attribute_root.get("display") is not None:
            raise NotImplementedError("BRD-style Attributes not supported yet")
        

        if attribute_root.getparent().tag == "technology":
            from_library = True;
        elif attribute_root.getparent().tag == "part":
            from_library = False
        else:
            assert False
            
        n = Attribute(
            name=attribute_root.get("name"),
            value=attribute_root.get("value"),
            constant=attribute_root.get("constant") != "no",
            from_library=from_library,
            in_library=from_library
        )
        return n
        
    def get_et (self):
        if self.in_library:
            return EagleUtil.make_attribute(
                name=self.name,
                value=self.value,
                constant= "yes" if self.constant else "no"
                )
        else:
            return EagleUtil.make_attribute(
                name=self.name,
                value=self.value,
                constant=None 
                )
        
class Sheet (EagleFilePart):
    def __init__ (self, plain=None, instances=None, busses=None, nets=None):
        EagleFilePart.__init__(self)
        if plain is None: plain = []
        if instances is None: instances = []
        if busses is None: busses = []
        if nets is None: nets = {}
    
        self.plain = plain
        self.instances = instances
        self.busses = busses
        self.nets = nets
        
    @classmethod
    def from_et (cls, sheet_root):
        assert sheet_root.tag == "sheet"
        sheet = cls()
        
        plain = EagleUtil.get_plain(sheet_root)
        for p in plain:
            sheet.add_plain(DrawingElement.from_et(p))
        
        instances = EagleUtil.get_instances(sheet_root)
        for instance in instances:
            new_instance = Instance.from_et(instance)
            sheet.add_instance(new_instance)
            
        busses = EagleUtil.get_buses(sheet_root)
        for b in busses:
            raise NotImplementedError("Busses not supported")
        
        nets = EagleUtil.get_nets(sheet_root)
        for net in nets:
            new_net = Net.from_et(net)
            sheet.add_net(new_net)
            
        return sheet

    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        return EagleUtil.make_sheet(
            plain=[p.get_et() for p in self.plain],
            instances=[instance.get_et() for instance in self.instances],
            busses=[bus.get_et() for bus in self.busses],
            nets=[net.get_et() for net in self.nets.values()]
        )

    def add_net(self, n):
        self.nets[n.name] = n
        n.parent = self

    def add_plain(self, n):
        self.plain.append(n)
        n.parent = self

    def add_instance(self, i):
        self.instances.append(i)
        i.parent = self
        
class Net (EagleFilePart):
    def __init__ (self, name=None, net_class="0", segments=None):
        EagleFilePart.__init__(self)
        if segments is None: segments = []
        
        self.name = name
        self.net_class = net_class
        self.segments = segments
        
    @staticmethod
    def from_et (net_root):
        assert net_root.tag == "net"
        net = Net()
        net.net_class = net_root.get("class")
        net.name = net_root.get("name")
        
        segments = EagleUtil.get_segments(net_root)
        
        for segment in segments:
            new_segment = Segment.from_et(segment)
            net.add_segment(new_segment)
            
        return net
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        return EagleUtil.make_net(
            name=self.name,
            net_class=self.net_class,
            segments=[segment.get_et() for segment in self.segments]
        )
    def add_segment(self, s):
        self.segments.append(s)
        s.parent = self
        
class Label (EagleFilePart):
    def __init__ (self, x=None, y=None, size=None, layer=None):
        EagleFilePart.__init__(self)
        self.x = x
        self.y = y
        self.size = size
        self.layer = layer
        
    @staticmethod
    def from_et (segment_root):
        assert segment_root.tag == "label"
        return Label(x=segment_root.get("x"),
                     y=segment_root.get("y"),
                     size=segment_root.get("size"),
                     layer=segment_root.get("layer"))
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        return EagleUtil.make_label(
            x=self.x,
            y=self.y,
            size=self.size,
            layer=self.layer
        )
        
class Junction(EagleFilePart):
    def __init__ (self, x=None, y=None):
        EagleFilePart.__init__(self)
        self.x=x
        self.y=y
        
    @staticmethod
    def from_et (junction_root):
        assert junction_root.tag == "junction"
        return Junction(x=junction_root.get("x"), y=junction_root.get("y"))

    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        return EagleUtil.make_junction(
            x=self.x,
            y=self.y,
        )
        
    
    def clone(self):
        return self._clone()

class Segment (EagleFilePart):
    def __init__ (self, pinrefs=None, portrefs=None, wires=None, junctions=None, labels=None):
        EagleFilePart.__init__(self)
        if pinrefs is None: pinrefs = []
        if portrefs is None: portrefs = []
        if wires is None: wires = []
        if junctions is None: junctions = []
        if labels is None: labels = []
    
        self.pinrefs = pinrefs
        self.portrefs = portrefs
        self.wires = wires
        self.junctions = junctions
        self.labels = labels
        
    @staticmethod
    def from_et (segment_root):
        assert segment_root.tag == "segment"
        segment = Segment()
        wires = EagleUtil.get_wires(segment_root)
        pinrefs = EagleUtil.get_pinrefs(segment_root)
        labels = EagleUtil.get_labels(segment_root)
        junctions = EagleUtil.get_junctions(segment_root)
        
        for wire in wires:
            segment.add_wire(Wire.from_et(wire))
            
        for pinref in pinrefs:
            segment.add_pinref(PinRef.from_et(pinref))
            
        for label in labels:
            segment.add_label(Label.from_et(label))

        for junction in junctions:
            segment.add_junction(Junction.from_et(junction))
            
        return segment
        
    def add_wire(self, w):
        self.wires.append(w);
        w.parent = self
    def add_label(self, w):
        self.labels.append(w);
        w.parent = self
    def add_junction(self, w):
        self.junctions.append(w);
        w.parent = self
    def add_pinref(self, w):
        self.pinrefs.append(w);
        w.parent = self

    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        #print "Getting et for segment", self.wires, self.pinrefs, self.labels
        return EagleUtil.make_segment(
            wires=[wire.get_et() for wire in self.wires],
            pinrefs=[pinref.get_et() for pinref in self.pinrefs],
            labels=[label.get_et() for label in self.labels],
            junctions=[junction.get_et() for junction in self.junctions]
        )
        
class Wire (DrawingElement):
    """
    EAGLE Wire.
    This class is used by EAGLE to draw straight lines. Nothing to do with electrical connections.
    """
    
    def __init__ (
            self, 
            x1=None, 
            x2=None, 
            y1=None, 
            y2=None, 
            width=None, 
            layer=None,
            curve=None,
            extent=None,
            style=None,
            cap=None,
    ):
        DrawingElement.__init__(self,layer)
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.width = width
        self.curve = curve
        self.extent = extent
        self.style = style
        self.cap = cap


    @staticmethod
    def from_et (wire_root):
        assert wire_root.tag == "wire"
        return Wire(
            x1=wire_root.get("x1"),
            x2=wire_root.get("x2"),
            y1=wire_root.get("y1"),
            y2=wire_root.get("y2"),
            width=wire_root.get("width"),
            curve=wire_root.get("curve"),
            layer=wire_root.get("layer"),
            style=wire_root.get("style"),
            cap=wire_root.get("cap"),
            extent=wire_root.get("extent")
        )
        
    def get_et (self):
        return EagleUtil.make_wire(
            x1=self.x1,
            x2=self.x2,
            y1=self.y1,
            y2=self.y2,
            width=self.width,
            curve=self.curve,
            layer=self.layer,
            style=self.style,
            cap=self.cap,
            extent=self.extent
        )

        
class PinRef (EagleFilePart):
    """
    EAGLE pinref tag.
    This is used in Net Segment to show that a Part's pin is connected to the Net."
    """
    
    
    def __init__ (self, part=None, gate=None, pin=None):
        EagleFilePart.__init__(self)
        self.part = part
        self.gate = gate
        self.pin = pin
        #print "Making pinref:", part, gate, pin
        
    @staticmethod
    def from_et (pinref_root):
        assert pinref_root.tag == "pinref"
        return PinRef(
            part=pinref_root.get("part"),
            gate=pinref_root.get("gate"),
            pin=pinref_root.get("pin")
        )
        
    def get_et (self):
        return EagleUtil.make_pinref(
            part=self.part,
            gate=self.gate,
            pin=self.pin
        )
        
class NetClass (EagleFilePart):
    """
    Eagle net class structure.
    This is called "class" in the EAGLE file but we can't use that in Python :package
    """
    
    def __init__ (self, number=None, name=None, width=None, drill=None):
        EagleFilePart.__init__(self)
        self.number = number
        self.name = name
        self.width = width
        self.drill = drill
        
    @staticmethod
    def from_et (root):
        assert root.tag == "class", "Trying to make a <class> section but got a <"+root.tag+"> section."
        number = root.get("number")
        name = root.get("name")
        width = root.get("width")
        drill = root.get("drill")
        
        return NetClass(number=number, name=name, width=width, drill=drill)
    
    def get_et (self):
        return EagleUtil.make_class (
            number=self.number,
            name=self.name,
            width=self.width,
            drill=self.drill
        )
        
    
class Layer (EagleFilePart):
    """
    Eagle layer structure.
    """
    def __init__ (self, number=None, name=None, color=None, fill=None, visible=None, active=None):
        EagleFilePart.__init__(self)
        self.number = number
        self.name = name
        self.color = color
        self.fill = fill
        self.visible = visible
        self.active = active
        
    def clone(self):
        return self._clone()

    @staticmethod    
    def from_et (et):
        #print "Layer from_et()"
        assert et.tag == "layer"
        layer = Layer(
            number=int(et.get("number")),
            name=et.get("name"),
            color=et.get("color"),
            fill=et.get("fill"),
            visible=et.get("visible"),
            active=et.get("active")
        )
        return layer
        
    #@staticmethod
    #def default_layers ():
        #print "Layer default_layers()"
        #et_layers = EagleUtil.get_default_layers()
        #et_layers = et_layers.findall("./layer")
        #layers = [Layer.from_et(None, layer) for layer in et_layers]
        #return layers
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        return EagleUtil.make_layer(
            number=str(self.number),
            name=self.name,
            color=self.color,
            fill=self.fill,
            visible=self.visible,
            active=self.active
        )

    @staticmethod
    def getLayer(efpart, l):
        #print l
        assert type(l) is str
        return str(efpart.get_root().layerNameToNumber(l))

    @staticmethod
    def stringLayer(efpart, l):
        #print l
        assert type(l) is str
        return str(efpart.get_root().layerNumberToName(int(l)))

class Instance (EagleFilePart):
    def __init__ (self, gate=None, part=None, x=None, y=None, rot=None):
        EagleFilePart.__init__(self)
        self.gate = gate
        self.part = part
        self.x = x
        self.y = y
        self.rot = rot
        
    @staticmethod
    def from_et (instance_root):
        assert instance_root.tag == "instance"
        return Instance(
            gate=instance_root.get("gate"),
            part=instance_root.get("part"),
            x=instance_root.get("x"),
            y=instance_root.get("y"),
            rot=instance_root.get("rot")
        )
    
    def get_et (self):
        return EagleUtil.make_instance(
            gate=self.gate,
            part=self.part,
            x=self.x,
            y=self.y,
            rot=self.rot
        )
    
class NetClass (EagleFilePart):
    """
    Eagle brd net class
    """
    def __init__(self, number=None, name=None,width=None,drill=None):
        EagleFilePart.__init__(self)
        self.number = number
        self.name = name
        self.width = width
        self.drill = drill

    @staticmethod
    def from_et(instance_root):
        assert instance_root.tag == "class"
        return NetClass(
            number = instance_root.get("number"),
            name= instance_root.get("name"),
            width = instance_root.get("width"),
            drill = instance_root.get("drill")
        )

    def get_et(self):
        return EagleUtil.make_class(
            number=self.number,
            name=self.name,
            width=self.width,
            drill= self.drill);

class ContactRef(EagleFilePart):

    def __init__(self, element=None,pad=None):
        """
        """
        EagleFilePart.__init__(self)
        self.element=element
        self.pad=pad

    def clone(self):
        return self._clone()
    
    @staticmethod
    def from_et(root):
        assert root.tag == "contactref"
        return ContactRef(
            element=root.get("element"),
            pad=root.get("pad")
        )

    def get_et(self):
        return EagleUtil.make_contactref(
            element=self.element,
            pad=self.pad
        )

class Description(EagleFilePart):

    def __init__(self, language=None):
        """
        """
        EagleFilePart.__init__(self)
        self.language=language

    @staticmethod
    def from_et(root):
        assert root.tag == "description"
        return Description(
            language=root.get("language")
        )

    def get_et(self):
        return EagleUtil.make_description(
            language=self.language
        )

class Signal(EagleFilePart):

    def __init__(self, name=None,contactrefs=None, wires=None):
        """
        """
        EagleFilePart.__init__(self)
        self.name=name
        if contactrefs is None:
            self.contactrefs=[]
        if wires is None:
            self.wires=[]
            
    def clone(self):
        n = self._clone()
        n.contactrefs = []
        n.wires = []
        [n.add_contactref(i.clone()) for i in self.contactrefs]
        [n.add_wire(i.clone()) for i in self.wires]
        
    @staticmethod
    def from_et(root):
        assert root.tag == "signal"
        n = Signal(name=root.get("name"))
        for cr in EagleUtil.get_contactrefs(root):
            c = ContactRef.from_et(cr)
            n.add_contactref(c)
            
        for cr in EagleUtil.get_wires(root):
            c = Wire.from_et(cr)
            n.add_wire(c)
            
        return n

    def get_et(self):
        n = EagleUtil.make_signal(name=self.name)
        
        return EagleUtil.make_signal(
            name=self.name,
            contactrefs=[c.get_et() for i in self.contactrefs]
        )

    def add_contactref(self, c):
        self.contactrefs.append(c)
        c.parent = self

    def add_wire(self, c):
        self.wires.append(c)
        c.parent = self
        
class Param(EagleFilePart):

    def __init__(self, name=None,value=None):
        """
        """
        EagleFilePart.__init__(self)
        self.name=name
        self.value=value

    @staticmethod
    def from_et(root):
        assert root.tag == "param"
        return Param(
            name=root.get("name"),
            value=root.get("value")
        )

    def get_et(self):
        return EagleUtil.make_param(
            name=self.name,
            value=self.value
        )

class Element(EagleFilePart):

    def __init__(self, name=None,value=None,package=None,x=None,y=None):
        """
        """
        EagleFilePart.__init__(self)
        self.name=name
        self.value=value
        self.package=package
        self.value=value
        self.x=x
        self.y=y

    @staticmethod
    def from_et(root):
        assert root.tag == "element"
        return Element(
            name=root.get("name"),
            value=root.get("value"),
            package=root.get("package"),
            x=root.get("x"),
            y=root.get("y")
        )

    def get_et(self):
        return EagleUtil.make_element(
            name=self.name,
            value=self.value,
            package=self.package,
            x=self.x,
            y=self.y
        )

class Pass(EagleFilePart):

    def __init__(self, name=None,refer=None,params=None):
        """
        """
        EagleFilePart.__init__(self)
        self.name = name
        if params is None:
            self.params = []
        else:
            self.params = params
        self.refer = refer
        

    @staticmethod
    def from_et(root):
        assert root.tag == "pass"
        return Pass(
            name=root.get("name"),
            params=root.get("params"),
            refer=root.get("refer")
        )

    def get_et(self):
        return EagleUtil.make_pass(
            name=self.name,
            params=[i.get_et() for i in self.params],
            refer=self.refer
        )
 
    
class Polygon(DrawingElement):

    def __init__(self,
                 width=None,
                 layer=None,
                 spacing=None,
                 pour=None,
                 isolate=None,
                 orphans=None,
                 thermals=None,
                 rank=None,
                 vertices=None):
        """
        """
        DrawingElement.__init__(self,layer)

        self.width=width
        self.layer=layer
        self.spacing=spacing
        self.pour=pour
        self.isolate=isolate
        self.orphans=orphans
        self.thermals=thermals
        self.rank=rank
        
        self.vertices = [] if vertices is None else vertices
            
    def clone(self):
        n = self._clone()
        n.vertices = []
        [n.add_vertex(i.clone()) for i in self.vertices]
        
    @staticmethod
    def from_et(root):
        assert root.tag == "polygon"
        n = Polygon()
        n.width = root.get("width")
        n.layer = root.get("layer")
        n.spacing = root.get("spacing")
        n.pour = root.get("pour")
        n.isolate = root.get("isolate")
        n.orphans = root.get("orphas")
        n.thermals = root.get("thermals")
        n.rang = root.get("rank")
        
        for v in EagleUtil.get_vertices(root):
            nv = Vertex.from_et(v)
            n.add_vertex(nv)
            
        return n

    def get_et(self):
        return EagleUtil.make_polygon(
            width=self.width,
            layer=self.layer,
            spacing=self.spacing,
            pour=self.pour,
            isolate=self.isolate,
            orphans=self.orphans,
            thermals=self.thermals,
            rank=self.rank,
            vertices = [i.get_et() for i in self.vertices])

    def add_vertex(self, c):
        self.vertices.append(c)
        c.parent = self

class Vertex(EagleFilePart):

    def __init__(self, x=None, y=None, curve=None):
        """
        """
        EagleFilePart.__init__(self)
        self.x = x
        self.y = y
        self.curve = curve
        
    def clone(self):
        return self._clone()
    
    @staticmethod
    def from_et(root):
        assert root.tag == "vertex"
        return Vertex(
            x=root.get("x"),
            y=root.get("y"),
            curve=root.get("curve")
        )

    def get_et(self):
        return EagleUtil.make_vertex(
            x=self.x,
            y=self.y,
            curve=self.curve
        )

