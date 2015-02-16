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
    def __init__(self, parent=None):
        assert isinstance(self, EagleFilePart)
        self.parent = parent

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
            

class EagleFile(EagleFilePart):

    DTD = ET.DTD(StringIO.StringIO(eagleDTD.DTD))

    def __init__ (self):
        EagleFilePart.__init__(self,None)
        self.layersByName = {}
        self.layersByNumber = {}
        self.filename= None

    def validate(self):
        return EagleFile.DTD.validate(self.get_et())
        
    def write (self, filename):
        """
        Exports the Schematic to an EAGLE schematic file.
        
        """
        self.check_sanity()
        if not self.validate():
            f = open(filename + ".broken.xml", "w")
            f.write(ET.tostring(ET.ElementTree(self.get_et()),pretty_print=True))
            raise HighEagleError("element tree does not validate" + str(EagleFile.DTD.error_log.filter_from_errors()[0]))
        else:
            f = open(filename, "w")
            f.write(ET.tostring(ET.ElementTree(self.get_et()),pretty_print=True))

    def add_layer (self, layer):
        #print "Schematic add_layer()"
        assert isinstance(layer, Layer)
        self.layersByNumber[int(layer.number)] = layer
        self.layersByName[layer.name] = layer
        layer.parent = self
        #print str(layer)
        #self.check_sanity()
        
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
            raise NotImplementedError("Remove layer by name")
        elif type(layer) is int:
            raise NotImplementedError("Remove layer by number")
        elif isinstance(layer, Layer):
            self.layersByName[layer.name].parent = None
            del self.layersByName[layer.name]
            del self.layersByNumber[layer.number]
        else:
            raise HighEagleError("Can't remove layer by " + str(type(layer)))
            
    def mergeLayersFromEagleFile(self, ef, force=False):
        for srcLayer in ef.get_layers().values():
            for dstLayer in self.get_layers().values():
                if ((srcLayer.name == dstLayer.name and srcLayer.number != dstLayer.number) or 
                    (srcLayer.name != dstLayer.name and srcLayer.number == dstLayer.number)):
                    if force:
                        self.remove_layer(dstLayer)
                    else:
                        raise HighEagleError("Layer mismatch: " + ef.filename +" <" + str(srcLayer.number) + ", '" + srcLayer.name +"'>; " + self.filename +" = <" + str(dstLayer.number) + ", '" + dstLayer.name +"'>;")
            if srcLayer.name not in self.get_layers():
                self.add_layer(srcLayer.clone())

    def get_manifest(self):
        raise NotImplementedError("Manifest for " + str(type(self)))

class Schematic (EagleFile):
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
        EagleFile.__init__(self)
        self.tree = None
        self.root = None
    
        self.settings = {}
        self.grid = {}
        
        for layer in Layer.default_layers():
            self.add_layer(layer)
        
        self.libraries = {}
        self.attributes = {}
        self.variantdefs = {}
        self.classes = {}
        self.parts = {}
        self.sheets = []

    @staticmethod
    def from_file (filename):
        """
        Loads a Schematic from an EAGLE .sch file.
        """
        tree = ET.parse(filename)
        root = tree.getroot()
        sch = Schematic.from_et(root)
        sch.filename =filename
        sch.check_sanity()
        return sch
        
    @staticmethod
    def from_et (et):
        """
        Loads a Schematic from an ElementTree.Element representation.
        """
        sch = Schematic()
        sch.tree = ET.ElementTree(et)
        
        # get sections
        settings = EagleUtil.get_settings(et)
        grid = EagleUtil.get_grid(et)
        layers = EagleUtil.get_layers(et)
        libraries = EagleUtil.get_libraries(et)
        attributes = EagleUtil.get_attributes(et)
        variantdefs = EagleUtil.get_variantdefs(et)
        classes = EagleUtil.get_classes(et)
        parts = EagleUtil.get_parts(et)
        #assert len(parts) > 0
        sheets = EagleUtil.get_sheets(et)
        
        #transform
        #print "Working on settings.", "Found", len(settings)
        for setting in settings:
            for key in setting.attrib:
                sch.settings[key] = setting.attrib[key]
                #print "Got:", key, setting.attrib[key]
                
        #print sch.settings
                
        for key in grid.attrib:
            sch.grid[key] = grid.attrib[key]
            
        for layer in layers:
            new_layer = Layer.from_et(sch,layer)
            sch.add_layer(new_layer)
            
        assert len(sch.get_layers()) > 0, "No layers in schematic."
        
        for library in libraries:
            #print library
            new_lib = Library.from_et(sch,library) #aoeu
            sch.add_library(new_lib)
            
        for attribute in attributes:
            raise NotImplementedError("Sheet attributes support not implemented")
            
        for variantdef in variantdefs:
            raise NotImplementedError("Sheet variant support not implemented")
            
        for net_class in classes:
            #print net_class
            new_class = NetClass.from_et(sch,net_class)
            sch.add_class(new_class)

        for part in parts:
            #print part
            new_part = Part.from_et(sch,part, schematic=sch)
            sch.add_part(new_part)
            
        #assert len(sch.parts) > 0
            
        for sheet in sheets:
            #print sheet
            new_sheet = Sheet.from_et(sch,sheet)
            sch.add_sheet(new_sheet)
        
        return sch

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
        #raise NotImplementedError("Adding parts not implemented")
        # add part to schematic
        # add part to sheet_index
        # make sure part is in library
        
    def add_class (self, c):
        """
        Adds a part to the schematic.
        All gates are placed on the given sheet (default sheet 0).
        """
        self.classes[c.name] = c
        c.parent = self

        
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
        
        eagle = EagleUtil.make_eagle()
        EagleUtil.set_settings(eagle, self.settings)
        EagleUtil.set_grid(eagle)
        
        for layer in self.get_layers().values():
            EagleUtil.add_layer(eagle, layer.get_et())

        for library in self.libraries.values():
            EagleUtil.add_library(eagle, library.get_et())
            
            
        for attribute in self.attributes:
            pass
            
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
        for part in self.parts.values():
            EagleUtil.add_part(eagle, part.get_et())
            
        #ET.dump(eagle) 
            
        #print   
        #print "Adding sheets"
        for i, sheet in enumerate(self.sheets):
            EagleUtil.add_sheet(eagle, sheet.get_et())
            #print "Sheet", i
            #ET.dump(eagle) 
        if len(self.sheets) == 0:
            EagleUtil.add_sheet(eagle, EagleUtil.make_empty_sheet())
            
        #ET.dump(eagle)    
            
        return eagle

    def get_parts(self):
        return self.parts
    
    def add_library(self, library):
        self.libraries[library.name] = library
        library.parent = self

    def get_libraries(self):
        return libraries

    def get_library(self, l):
        if l not in self.libraries:
            raise HighEagleError("Missing library '" + str(l) + "' in " + self.filename)
        return self.libraries[l]

class Pin (EagleFilePart):
    """
    EAGLE pin tag.
    This is a connectible pin on a circuit Symbol. It maps to a Pad or SMD on a Package.
    """
    
    def __init__ (self, parent=None, name=None, x=None, y=None, visible=None, length=None, direction=None, swaplevel=None, rot=None):
        EagleFilePart.__init__(self,parent)
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
    def from_et (cls, parent,pin_root):
        return cls(
            parent=parent,
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
        self.tree = None
        self.root = None
    
        self.settings = {}
        self.grid = {}
        self.name = None

        for layer in Layer.default_layers():
            self.add_layer(layer)
        
        self.libraries = None

    @staticmethod
    def from_file(filename):
        tree = ET.parse(filename)
        root = tree.getroot()
        r = LibraryFile.from_et(root)
        r.filename =filename
        r.name = filename.replace(".lbr","")
        r.library.name = r.name
        r.check_sanity()
        return r

    @staticmethod
    def from_et (et):
        """
        Loads a Library file from an ElementTree.Element representation.
        """
        lbr = LibraryFile()
        lbr.tree = ET.ElementTree(et)
        
        # get sections
        settings = EagleUtil.get_settings(et)
        grid = EagleUtil.get_grid(et)
        layers = EagleUtil.get_layers(et)
        library = EagleUtil.get_library(et)
        
        #transform
        for setting in settings:
            for key in setting.attrib:
                lbr.settings[key] = setting.attrib[key]
                #print "Got:", key, setting.attrib[key]
                
        for key in grid.attrib:
            lbr.grid[key] = grid.attrib[key]
            
        for layer in layers:
            new_layer = Layer.from_et(lbr,layer)
            lbr.add_layer(new_layer)
            
        assert len(lbr.get_layers()) > 0, "No layers in schematic."
        
        lbr.library = Library.from_et(lbr,library)

        return lbr

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
        
        for layer in self.get_layers().values():
            EagleUtil.add_layer(eagle, layer.get_et())

        EagleUtil.add_library_to_library_file(eagle, self.library.get_et())
            
        return eagle


    def get_library_copy(self):
        return copy.deepcopy(self.library)
        
class Library (EagleFilePart):
    def __init__ (self, parent=None, name=None, description="", packages=None, symbols=None, devicesets=None):        
        EagleFilePart.__init__(self,parent)
        self.name = name
        if packages is None: packages = {}
        if symbols is None: symbols = {}
        if devicesets is None: devicesets = {}
        
        self.description = description
        self.packages = packages
        self.symbols = symbols
        self.devicesets = devicesets
        
    @classmethod
    def from_et (cls, parent, library_root):
        assert library_root.tag == "library"
        lib = cls(parent, name=library_root.get("name"))
        #print "Loading library:", lib.name
        lib.description = EagleUtil.get_description(library_root)
        
        packages = EagleUtil.get_packages(library_root)
        symbols = EagleUtil.get_symbols(library_root)
        devicesets = EagleUtil.get_devicesets(library_root)
        
        lib.packages = {}
        for package in packages:
            new_package = Package.from_et(lib, package)
            assert new_package.name not in lib.packages, "Cannot have duplicate package names: "+new_package.name
            lib.add_package(new_package)
            
        lib.symbols = {}
        for symbol in symbols:
            new_symbol = Symbol.from_et(lib, symbol)
            assert new_symbol.name not in lib.symbols, "Cannot have duplicate symbol names: "+new_symbol.name
            lib.add_symbol(new_symbol)
            
        lib.devicesets = {}
        for deviceset in devicesets:
            new_deviceset = DeviceSet.from_et(lib, deviceset)
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
    def __init__ (self, parent=None, name=None, contacts=None, drawingElements=None):        
        EagleFilePart.__init__(self,parent)
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
        n = Package(parent=None,
                    name=self.name)
        for i in self.drawingElements:
            n.add_drawingElement(i.clone())
        for i in self.contacts.values():
            n.add_contact(i.clone())
        return n

    @staticmethod
    def from_et (parent, package_root):
        new_package = Package(parent=parent)
        new_package.name = None
        new_package.contacts = {}
        new_package.drawingElement = []
        
        new_package.name = package_root.get("name")
        pads = EagleUtil.get_pads(package_root)
        smds = EagleUtil.get_smds(package_root)
        drawingElements = EagleUtil.get_drawingElements(package_root)
        
        for pad in pads:
            new_pad = Pad.from_et(new_package,pad)
            assert new_pad.name not in new_package.contacts, "Cannot add pad with duplicate name: "+new_pad.name
            new_package.add_contact(new_pad)
        
        for smd in smds:
            new_smd = SMD.from_et(new_package,smd)
            assert new_smd.name not in new_package.contacts, "Cannot add smd with duplicate name: "+new_smd.name
            new_package.add_contact(new_smd)
            
        for drawingElement in drawingElements:
            new_drawingElement = DrawingElement.from_et(new_package,drawingElement)
            new_package.drawingElements.append(new_drawingElement)
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
  
    def __init__ (self, parent=None, name=None, x=None, y=None, drill=None, diameter=None, shape=None, rot=None):        
        EagleFilePart.__init__(self,parent)
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
    def from_et (parent, pad_root):
        assert pad_root.tag == "pad"
        return Pad(
            parent=parent,
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
                 parent=None,
                 layer=None):
        EagleFilePart.__init__(self, parent)
        ef = self.get_file()
        assert ef is not None

        if type(layer) is int:
            assert layer in ef.layersByNumber
            self.layer = ef.layersByNumber[layer].name
        elif type(layer) is str:
            assert layer in ef.layersByName
            self.layer = layer
        
    @staticmethod
    def from_et (parent,drawing_root):
        if drawing_root.tag == "wire":
            return Wire.from_et(parent, drawing_root)
        elif drawing_root.tag == "circle":
            return Circle.from_et(parent, drawing_root)
        elif drawing_root.tag == "rectangle":
            return Rectangle.from_et(parent, drawing_root)
        elif drawing_root.tag == "text":
            return Text.from_et(parent, drawing_root)
        else:
            raise Exception("Don't know how to parse "+drawing_root.tag+" tag as a drawing tag.")        

class Rectangle (DrawingElement):
    """
    EAGLE rectangle tag.
    This is used to draw text on the schematic or board.
    """
    def __init__ (
        self, 
        parent=None,
        x1=None, 
        y1=None, 
        x2=None, 
        y2=None,
        layer=None, 
    ):
        DrawingElement.__init__(self,parent, layer)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        
    def clone(self):
        return self._clone()


    @staticmethod
    def from_et (parent, rectangle_root):
        assert rectangle_root.tag == "rectangle"
        return Rectangle(
            parent=parent,
            x1=rectangle_root.get("x1"),
            y1=rectangle_root.get("y1"),
            x2=rectangle_root.get("x2"),
            y2=rectangle_root.get("y2"),
            layer=Layer.stringLayer(parent, rectangle_root.get("layer"))
        )
        
    def get_et (self):
        return EagleUtil.make_rectangle(
            x1=self.x1,
            x2=self.x2,
            y1=self.y1,
            y2=self.y2,
            layer=Layer.etLayer(self,self.layer)
        )
        
class Text (DrawingElement):
    """
    EAGLE text tag.
    This is used to draw text on the schematic or board.
    """
    def __init__ (self, parent=None, x=None, y=None, size=None, layer=None, text=None):        
        DrawingElement.__init__(self,parent,layer)
        self.x = x
        self.y = y
        self.size = size
        self.text = text
        
    def clone(self):
        return self._clone()


    @staticmethod
    def from_et (parent, text_root):
        assert text_root.tag == "text"
        return Text(
            parent=parent,
            x=text_root.get("x"),
            y=text_root.get("y"),
            size=text_root.get("size"),
            layer=Layer.stringLayer(parent, text_root.get("layer")),
            text=text_root.text
        )
        
    def get_et (self):
        return EagleUtil.make_text(
            x=self.x,
            y=self.y,
            size=self.size,
            layer=Layer.etLayer(self,self.layer),
            text=self.text
        )
        
class Circle (DrawingElement):
    """
    EAGLE circle tag.
    This is used to draw a circle on the schematic or board.
    """
    def __init__ (self, parent=None, x=None, y=None, radius=None, width=None, layer=None):
        DrawingElement.__init__(self,parent,layer)
        self.x = x
        self.y = y
        self.radius = radius
        self.width = width

    def clone(self):
        return self._clone()
        
    @staticmethod
    def from_et (parent, circle_root):
        assert circle_root.tag == "circle"
        return Circle(
            parent=parent,
            x=circle_root.get("x"),
            y=circle_root.get("y"),
            radius=circle_root.get("radius"),
            width=circle_root.get("width"),
            layer=Layer.stringLayer(parent, circle_root.get("layer")))
        
    def get_et (self):
        return EagleUtil.make_circle(
            x=self.x,
            y=self.y,
            radius=self.radius,
            width=self.width,
            layer=Layer.etLayer(self,self.layer)
        )
        

        
class SMD (EagleFilePart):
    """
    EAGLE smd tag.
    This is a smd contact in a Package that gets mapped to a Pin on a Gate.
    """
  
    def __init__ (self, parent=None, name=None, x=None, y=None, dx=None, dy=None, layer=None, rot=None):
        EagleFilePart.__init__(self,parent)
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
    def from_et (parent, smd_root):
        assert smd_root.tag == "smd"
        return SMD(
            parent=parent,
            name=smd_root.get("name"),
            x=smd_root.get("x"),
            y=smd_root.get("y"),
            dx=smd_root.get("dx"),
            dy=smd_root.get("dy"),
            layer=Layer.stringLayer(parent, smd_root.get("layer")),
            rot=smd_root.get("rot")
        )        
        
    def get_et (self):
        return EagleUtil.make_SMD(
            name=self.name,
            x=self.x,
            y=self.y,
            dx=self.dx,
            dy=self.dy,
            layer=Layer.etLayer(self,self.layer),           
            rot=self.rot
        )
               
class Symbol (EagleFilePart):
    """
    EAGLE symbol section.
    This section holds circuit diagram symbols that can be used as gates for Devices and Parts.
    """
    
    def __init__ (self, parent=None, name=None, drawingElements=None, pins=None):
        EagleFilePart.__init__(self,parent)
        self.name = name
        
        if drawingElements is None: 
            drawingElements = []
        if pins is None: pins = {}
        
        self.drawingElements = drawingElements
        self.pins = pins
    
    def clone(self):
        n = Symbol(parent=None,
                   name=self.name)
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
    def from_et (cls, parent, symbol_root):
        assert symbol_root.tag == "symbol"
        
        symbol = cls(parent)
        symbol.name = symbol_root.get("name")
        
        drawingElements = EagleUtil.get_drawingElements(symbol_root)
        for drawing in drawingElements:
            symbol.add_drawingElement(DrawingElement.from_et(symbol, drawing))
            
        pins = EagleUtil.get_pins(symbol_root)
        for pin in pins:
            symbol.add_pin(Pin.from_et(symbol, pin))

        return symbol

    def get_et (self):
        return EagleUtil.make_symbol(
            name=self.name,
            drawingElements=[drawing.get_et() for drawing in self.drawingElements],
            pins=[pin.get_et() for pin in self.pins.values()]
        )
    
class Part (EagleFilePart):
    def __init__ (self, parent=None, name=None, library=None, deviceset=None, device=None, package=None, value=None, schematic=None, technology=None):
        EagleFilePart.__init__(self,parent)
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

    @staticmethod
    def from_et (parent, root, schematic=None):
        name = root.get("name")
        library = root.get("library")
        deviceset = root.get("deviceset")
        device = root.get("device")
        package = root.get("package")
        value = root.get("value")
        technology =root.get("technology")

        if technology is None:
            technology = ""

        part = Part(parent=parent,
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
                part.add_attribute(Attribute.from_et(part, i))
        
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

        return EagleUtil.make_part(
            name=self.name,
            deviceset=self.deviceset,
            library=self.library,
            device=self.device,
            value=str(self.value),
            attributes=attrs
        )
        

    def add_attribute(self,attribute):
        self.attributes[attribute.name] = attribute
        attribute.parent = self

    def get_library(self):
        """
        Get the library that contains this part
        """
        try:
            lib = self.schematic.libraries[self.library]
        except:
            raise EagleFormatError("Missing library '" + self.library + "' for part '" + self.name + "'.")
        return lib

    def get_deviceset(self):
        """
        Get the deviceset for this part.
        """

        lib = self.get_library();
        try:
            deviceset = lib.devicesets[self.deviceset]
        except:
            raise EagleFormatError("Missing device set '" + self.library + ":" + self.deviceset + "' for part '" + self.name + "' in file " +self.get_file().filename +".")
        
        return deviceset
        
    def get_device(self):
        """
        Get the library entry for this part
        """
        deviceset = self.get_deviceset()

        try:
            device = deviceset.devices[self.device]
        except:
            raise EagleFormatError("Missing device '" + self.library + ":" + self.deviceset + ":" + self.device  + "' for part '" + self.name + "'.")
        
        return device

    def get_technology(self):
        """
        Get the library entry for this part
        """
        device = self.get_device()

        try:
            tech = device.technologies[self.technology]
        except:
            raise EagleFormatError("Missing technology '" + self.library + ":" + self.deviceset + ":" + self.device  + ":" + self.technology+  "' for part '" + self.name + "'.")
        
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
        try:
            package = lib.packages[device.package];
        except:
            raise EagleFormatError("Missing package '" + device.package + "' for part '" + self.name + "'.")
        return package
        
    def get_gate(self):
        """
        Get the library entry for this part
        """
        deviceset = self.get_deviceset();
        lib = self.get_library();
        assert deviceset.gates.len == 1
        try:
            gate = lib.symbols[deviceset.gates["G$1"]];
        except:
            raise EagleFormatError("Missing gate '" + deviceset.gate["G$1"] + "' for part '" + self.name + "'.")
        return gate
    
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
    def __init__ (self, parent=None, name=None, prefix=None, devices=None, description="", gates=None):
        EagleFilePart.__init__(self,parent)
    
        if devices is None: devices = {}
        if gates is None: gates = {}
    
        self.name = name
        self.prefix = prefix
        self.description = description
        self.gates = gates
        self.devices = devices
        
    @classmethod
    def from_et (cls, parent, deviceset_root):
        deviceset = cls(parent=parent, name=deviceset_root.get("name"))
        deviceset.description = EagleUtil.get_description(deviceset_root)
        
        gates = EagleUtil.get_gates(deviceset_root)
        devices = EagleUtil.get_devices(deviceset_root)
        
        for gate in gates:
            new_gate = Gate.from_et(deviceset, gate)
            name = new_gate.name
            deviceset.gates[name] = new_gate
            
        for device in devices:
            new_device = Device.from_et(deviceset, device)
            name = new_device.name
            deviceset.devices[name] = new_device
        
        return deviceset
        
    def clone(self):
        n = DeviceSet(parent=None,
                      name=self.name)
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
    
    def __init__ (self, parent=None, name=None, symbol=None, x=0, y=0):
        EagleFilePart.__init__(self,parent)
        self.name = name
        self.symbol = symbol
        self.x = x
        self.y = y
        
    def clone(self):
        return self._clone()

    @staticmethod
    def from_et (parent, gate_root):
        gate = Gate(
            parent=parent,
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
        
        
class Connect (EagleFilePart):
    """
    EAGLE connect tag.
    This maps a Gate's Pin to a Package's Pad or SMD. Subsection of Device.
    """
    
    def __init__ (self, parent=None, gate=None, pin=None, pad=None):
        EagleFilePart.__init__(self,parent)
        self.gate = gate
        self.pin = pin
        self.pad = pad

    def clone(self):
        return self._clone()
        
    @classmethod
    def from_et (cls, parent,connect_root):
        assert connect_root.tag == "connect"
        return cls(
            parent=parent,
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
    def __init__ (self, parent=None, name=None, package=None, connects=None, technologies=None):
        EagleFilePart.__init__(self,parent)
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
    def from_et (cls, parent, device_root):
        assert device_root.tag == "device"
        device = cls(parent=parent)
        
        device.name = device_root.get("name")
        device.package = device_root.get("package")
        
        connects = EagleUtil.get_connects(device_root)
        for connect in connects:
            device.add_connect(Connect.from_et(device, connect))
        
        technologies = EagleUtil.get_technologies(device_root)
        for technology in technologies:
            device.add_technology(Technology.from_et(device, technology))
                        
        return device
        
    def clone(self):
        n = Device(parent=None,
                   name=self.name,
                   package=self.package)
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
    
    def __init__ (self, parent=None, name=None, attributes=None):
        EagleFilePart.__init__(self,parent)
        if attributes is None: attributes = {}
        self.attributes = attributes
        self.name = name
        
    def clone(self):
        n = Technology(parent=None,
                       name=self.name)
        for i in self.attributes.values():
            n.add_attribute(i.clone())
        return n

    @classmethod
    def from_et (cls, parent, technology_root):
        tech = cls(parent=parent)
        tech.name = technology_root.get("name")
        attributes = EagleUtil.get_attributes(technology_root)
        
        for attribute in attributes:
            tech.add_attribute(Attribute.from_et(tech,attribute))
 
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
    
    def __init__ (self, parent=None, name=None, value=None, constant=None, from_library=False, in_library=True):
        EagleFilePart.__init__(self,parent)
        self.name = name
        self.value = value
        self.constant = constant
        self.from_library = from_library
        self.in_library = in_library

    def __str__(self):
        return self.name + " = '" + self.value + "' [const=" + str(self.constant) + ";lib=" + str(self.from_library) +"]";

    def clone(self):
        return Attribute(parent=None,
                         name=self.name,
                         value=self.value,
                         constant=self.constant,
                         from_library=self.from_library,
                         in_library=self.in_library)
                         
    @staticmethod
    def from_et (parent, attribute_root):
        assert attribute_root.tag == "attribute"
        #ET.dump(attribute_root);
        #ET.dump(attribute_root.getparent());
        if attribute_root.getparent().tag == "technology":
            from_library = True;
        elif attribute_root.getparent().tag == "part":
            from_library = False
        else:
            assert False
            
        n = Attribute(
            parent=parent,
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
    def __init__ (self, parent=None, plain=None, instances=None, busses=None, nets=None):
        EagleFilePart.__init__(self,parent)
        if plain is None: plain = []
        if instances is None: instances = []
        if busses is None: busses = []
        if nets is None: nets = {}
    
        self.plain = plain
        self.instances = instances
        self.busses = busses
        self.nets = nets
        
    @classmethod
    def from_et (cls, parent, sheet_root):
        assert sheet_root.tag == "sheet"
        sheet = cls(parent=parent)
        
        plain = EagleUtil.get_plain(sheet_root)
        for p in plain:
            pass #process into drawing types
        sheet.plain = plain
        
        instances = EagleUtil.get_instances(sheet_root)
        for instance in instances:
            new_instance = Instance.from_et(sheet,instance)
            sheet.instances.append(new_instance)
            
        busses = EagleUtil.get_buses(sheet_root)
        sheet.busses = busses
        
        nets = EagleUtil.get_nets(sheet_root)
        for net in nets:
            new_net = Net.from_et(sheet, net)
            sheet.nets[new_net.name] = new_net
            
        return sheet
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        return EagleUtil.make_sheet(
            plain=[p for p in self.plain],
            instances=[instance.get_et() for instance in self.instances],
            busses=[bus.get_et() for bus in self.busses],
            nets=[net.get_et() for net in self.nets.values()]
        )
            
        
class Net (EagleFilePart):
    def __init__ (self, parent=None, name=None, net_class="0", segments=None):
        EagleFilePart.__init__(self,parent)
        if segments is None: segments = []
        
        self.name = name
        self.net_class = net_class
        self.segments = segments
        
    @staticmethod
    def from_et (parent, net_root):
        assert net_root.tag == "net"
        net = Net(parent=parent)
        net.net_class = net_root.get("class")
        net.name = net_root.get("name")
        
        segments = EagleUtil.get_segments(net_root)
        
        for segment in segments:
            new_segment = Segment.from_et(net, segment)
            net.segments.append(new_segment)
            
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
        
class Label (EagleFilePart):
    def __init__ (self, parent=None, x=None, y=None, size=None, layer=None):
        EagleFilePart.__init__(self,parent)
        self.x = x
        self.y = y
        self.size = size
        self.layer = layer
        
    @staticmethod
    def from_et (parent, segment_root):
        assert segment_root.tag == "label"
        return Label(parent=parent,
                     x=segment_root.get("x"),
                     y=segment_root.get("y"),
                     size=segment_root.get("size"),
                     layer=Layer.stringLayer(parent, segment_root.get("layer")))
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        return EagleUtil.make_label(
            x=self.x,
            y=self.y,
            size=self.size,
            layer=Layer.etLayer(self,self.layer)
        )
        
class Junction(EagleFilePart):
    def __init__ (self, parent=None, x=None, y=None):
        EagleFilePart.__init__(self,parent)
        self.x=x
        self.y=y
        
    @staticmethod
    def from_et (parent, junction_root):
        assert junction_root.tag == "junction"
        return Junction(parent=parent,x=junction_root.get("x"), y=junction_root.get("y"))

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
    def __init__ (self, parent=None, pinrefs=None, portrefs=None, wires=None, junctions=None, labels=None):
        EagleFilePart.__init__(self,parent)
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
    def from_et (parent, segment_root):
        assert segment_root.tag == "segment"
        segment = Segment(parent=parent)
        wires = EagleUtil.get_wires(segment_root)
        pinrefs = EagleUtil.get_pinrefs(segment_root)
        labels = EagleUtil.get_labels(segment_root)
        junctions = EagleUtil.get_junctions(segment_root)
        
        for wire in wires:
            segment.add_wire(Wire.from_et(segment, wire))
            
        for pinref in pinrefs:
            segment.add_pinref(PinRef.from_et(segment, pinref))
            
        for label in labels:
            segment.add_label(Label.from_et(segment, label))

        for junction in junctions:
            segment.add_junction(Junction.from_et(segment, junction))
            
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
        parent=None,
        x1=None, 
        x2=None, 
        y1=None, 
        y2=None, 
        width=None, 
        layer=None,
        curve=None
    ):
        DrawingElement.__init__(self,parent,layer)
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.width = width
        self.curve = curve

    def clone(self):
        return self._clone()

    @staticmethod
    def from_et (parent, wire_root):
        assert wire_root.tag == "wire"
        return Wire(
            parent=parent,
            x1=wire_root.get("x1"),
            x2=wire_root.get("x2"),
            y1=wire_root.get("y1"),
            y2=wire_root.get("y2"),
            width=wire_root.get("width"),
            curve=wire_root.get("curve"),
            layer=Layer.stringLayer(parent, wire_root.get("layer"))
        )
        
    def get_et (self):
        return EagleUtil.make_wire(
            x1=self.x1,
            x2=self.x2,
            y1=self.y1,
            y2=self.y2,
            width=self.width,
            curve=self.curve,
            layer=Layer.etLayer(self,self.layer)
        )

        
class PinRef (EagleFilePart):
    """
    EAGLE pinref tag.
    This is used in Net Segment to show that a Part's pin is connected to the Net."
    """
    
    
    def __init__ (self, parent=None, part=None, gate=None, pin=None):
        EagleFilePart.__init__(self,parent)
        self.part = part
        self.gate = gate
        self.pin = pin
        #print "Making pinref:", part, gate, pin
        
    @staticmethod
    def from_et (parent,pinref_root):
        assert pinref_root.tag == "pinref"
        return PinRef(
            parent=parent,
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
    
    def __init__ (self, parent=None, number=None, name=None, width=None, drill=None):
        EagleFilePart.__init__(self,parent)
        self.number = number
        self.name = name
        self.width = width
        self.drill = drill
        
    @staticmethod
    def from_et (parent, root):
        assert root.tag == "class", "Trying to make a <class> section but got a <"+root.tag+"> section."
        number = root.get("number")
        name = root.get("name")
        width = root.get("width")
        drill = root.get("drill")
        
        return NetClass(parent=parent,number=number, name=name, width=width, drill=drill)
    
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
    def __init__ (self, parent=None, number=None, name=None, color=None, fill=None, visible=None, active=None):
        EagleFilePart.__init__(self,parent)
        self.number = number
        self.name = name
        self.color = color
        self.fill = fill
        self.visible = visible
        self.active = active
        
    def clone(self):
        return self._clone()

    @staticmethod    
    def from_et (parent, et):
        #print "Layer from_et()"
        assert et.tag == "layer"
        layer = Layer(
            parent=parent,
            number=int(et.get("number")),
            name=et.get("name"),
            color=et.get("color"),
            fill=et.get("fill"),
            visible=et.get("visible"),
            active=et.get("active")
        )
        return layer
        
    @staticmethod
    def default_layers ():
        #print "Layer default_layers()"
        et_layers = EagleUtil.get_default_layers()
        et_layers = et_layers.findall("./layer")
        layers = [Layer.from_et(None, layer) for layer in et_layers]
        return layers
        
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
    def etLayer(efpart, l):
        #print l
        assert type(l) is str
        return str(efpart.get_root().layerNameToNumber(l))

    @staticmethod
    def stringLayer(efpart, l):
        #print l
        assert type(l) is str
        return str(efpart.get_root().layerNumberToName(int(l)))

class Instance (EagleFilePart):
    def __init__ (self, parent=None, gate=None, part=None, x=None, y=None, rot=None):
        EagleFilePart.__init__(self,parent)
        self.gate = gate
        self.part = part
        self.x = x
        self.y = y
        self.rot = rot
        
    @staticmethod
    def from_et (parent, instance_root):
        assert instance_root.tag == "instance"
        return Instance(
            parent=parent,
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
    
