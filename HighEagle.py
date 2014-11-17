"""
This module's goal is to provide a python class-structured implementation of the EAGLE PCB file format.
All information in the schematic file is available as class attributes. 
Larger sections are available as classes.
List of sections with a name attribute are implemented as dicts, indexed on the sections name attribute.

The implementation is currently focused on the .sch circuit schematic file formate.
"""

import xml.etree.ElementTree as ET

import EagleUtil

class EagleFormatError (Exception):
    pass

class Schematic (object):
    """
    This is the top level for a circuit file.
    
    It contains libraries, parts, sheets, and some other information required by the EAGLE file format.
    """
    def __init__ (self):
        """
        Initialized an empty schematic or loads a schematic from a .sch file if a file name is specified.
        The empty schematic should be compatible with EAGLE and should open and close with no warnings or errors.
        """
        self.tree = None
        self.root = None
    
        self.settings = {}
        self.grid = {}
        self.layers = {}
        
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
        return Schematic.from_et(root)
        
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
        sheets = EagleUtil.get_sheets(et)
        
        #transform
        for setting in settings:
            for key in setting.attrib:
                self.settings[key] = setting.attrib[key]
        else:
            raise EagleFormatError("No settings found in EAGLE file.")
                
        for key in grid.attrib:
            self.grid[key] = grid.attrib[key]
            
        for layer in layers:
            new_layer = Layer.from_et(layer)
            self.layers[new_layer.number] = new_layer
        else:
            raise EagleFormatError("No layers found in EAGLE file.")
        
        for library in libraries:
            new_lib = Library.from_et(library)
            self.libraries[new_lib.name] = new_lib
            
        for attribute in attributes:
            pass
            
        for variantdef in variantdefs:
            pass
            
        for _class in classes:
            new_class = NetClass.from_et(_class)
            self.classes[new_class.name] = new_class
            
        for part in parts:
            new_part = Part.from_et(part)
            self.parts[new_part.name] = new_part
            
        for sheet in sheets:
            new_sheet = Sheet.from_et(sheet)
            self.sheets.append(new_sheet)
        
        
    def write (self, filename):
        """
        Exports the Schematic to an EAGLE schematic file.
        
        Not implemented yet.
        """
        ET.ElementTree(self.get_et()).write(filename)
        
    def add_part (part, sheet_index=0):
        """
        Adds a part to the schematic.
        All gates are placed on the given sheet (default sheet 0).
        """
        pass
        # add part to schematic
        # add part to sheet_index
        # make sure part is in library
        
    def add_layer (self, layer):
        #print "Schematic add_layer()"
        assert isinstance(layer, Layer)
        self.layers[layer.number] = layer
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        eagle = EagleUtil.empty_schematic()
        EagleUtil.set_settings(eagle, self.settings)
        EagleUtil.set_grid(eagle)
        
        for layer in self.layers.values():
            EagleUtil.add_layer(eagle, layer.get_et())
            
        for library in self.libraries:
            EagleUtil.add_library(eagle, library.get_et())
            
        for attribute in self.attributes:
            pass
            
        for varientdef in self.variantdefs:
            pass
            
        for _class in self.classes:
            EagleUtil.add_class(eagle, _class.get_et())
            
        for part in self.parts:
            EagleUtil.add_part(eagle, part.get_et())
            
        for sheet in self.sheets:
            EagleUtil.add_sheet(eagle, sheet.get_et())
        else:
            EagleUtil.add_sheet(eagle, EagleUtil.get_empty_sheet())
            
        ET.dump(eagle)    
            
        return eagle
        
class Library (object):
    def __init__ (self, name=None, description="", packages={}, symbols={}, devicesets={}):
        self.name = name
        self.description = description
        self.packages = packages
        self.symbols = symbols
        self.devicesets = devicesets
        
    def load_from_file (self, filename):
        """
        Overwrites the current Library with a new one loaded from the specified file name.
        """
        
    def load_from_et (self, root):
        """
        Loads a Library from an EAGLE .lbr file.
        """
        pass
        
    @staticmethod
    def from_et (root):
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        pass
        
    def get_part (self, name=None, deviceset=None, device=None, package=None):
        """
        Searches the library for a device that fits the specified parameters.
        """
        
        
class Part (object):
    def __init__ (self, name=None, library=None, deviceset=None, device=None, package=None):
        self.name = name
        self.library = library
        self.deviceset = deviceset
        self.device = device
        
    @staticmethod
    def from_et (root):
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        pass
        
class DeviceSet (object):
    def __init__ (self, name=None, prefix=None, devices={}, description="", gates={}):
        self.name = name
        self.prefix = prefix
        self.description = description
        self.gates = gates
        
    @staticmethod
    def from_et (root):
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        pass
        
class Device (object):
    def __init__ (self, name=None, technologies=[]):
        self.name = name
        self.technologies = technologies
        
    @staticmethod
    def from_et (root):
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        pass
        
class Sheet (object):
    def __init__ (self, plain=[], instances={}, busses=[], nets={}):
        self.plain = plain
        self.instances = instances
        self.busses = busses
        self.nets = nets
        
    @staticmethod
    def from_et (root):
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        pass
        
class Net (object):
    def __init__ (self, name=None, _class="0", segments=[]):
        self.name = name
        self._class = _class
        self.segments = segments
        
    @staticmethod
    def from_et (root):
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        pass
        
class Segment (object):
    def __init__ (self, pinrefs=[], wires=[]):
        self.pinrefs = pinrefs
        self.wires = wires
        
    @staticmethod
    def from_et (root):
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        pass
        
class NetClass (object):
    """
    Eagle net class structure.
    This is called "class" in the EAGLE file but we can't use that in Python :package
    """
    
    def __init__ (self, number=None, name=None, width=None, drill=None):
        self.number = number
        self.name = name
        self.width = width
        self.drill = drill
        
    @staticmethod
    def from_et (root):
        number = root.get("number")
        name = root.get("name")
        width = root.get("width")
        drill = root.get("drill")
        
        return NetClass(number=number, name=name, width=width, drill=drill)
    
class Layer (object):
    """
    Eagle layer structure.
    """
    def __init__ (self, number=None, name=None, color=None, fill=None, visible=None, active=None):
        self.number = number
        self.name = name
        self.color = color
        self.fill = fill
        self.visible = visible
        self.active = active
        
    @staticmethod    
    def from_et (et):
        #print "Layer from_et()"
        assert et.tag == "layer"
        layer = Layer(
            number=et.get("number"),
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
        layers = [Layer.from_et(layer) for layer in et_layers]
        return layers
        
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        return EagleUtil.make_layer(
            number=self.number,
            name=self.name,
            color=self.color,
            fill=self.fill,
            visible=self.visible,
            active=self.active
        )
    
    
    
    
    
    
    
    
    
    
    
    
    
    