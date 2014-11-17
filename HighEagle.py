"""
This module's goal is to provide a python class-structured implementation of the EAGLE PCB file format.
All information in the schematic file is available as class attributes. 
Larger sections are available as classes.
List of sections with a name attribute are implemented as dicts, indexed on the sections name attribute.

The implementation is currently focused on the .sch circuit schematic file formate.
"""

import xml.etree.ElementTree as ET

import EagleUtil

class Schematic (object):
    """
    This is the top level for a circuit file.
    
    It contains libraries, parts, sheets, and some other information required by the EAGLE file format.
    """
    def __init__ (self, filename=None):
        """
        Initialized an empty schematic or loads a schematic from a .sch file if a file name is specified.
        The empty schematic should be compatible with EAGLE and should open and close with no warnings or errors.
        """
        self.tree = None
        self.root = None
    
        self.settings = {}
        self.grid = {}
        self.layers = {}
        self.libraries = {}
        self.attributes = {}
        self.variantdefs = {}
        self.classes = {}
        self.parts = {}
        self.sheets = []
    
        if filename is not None:
            self.load_from_file (filename)
            
    def load_from_file (self, filename):
        """
        Overwrites the current Schematic with a new one loaded from the specified file name.
        Assumes that the current Schematic has been properly initialized.
        """
        
        self.tree = ET.parse(filename)
        self.root = self.tree.getroot()
        
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
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        eagle = EagleUtil.empty_schematic()
        EagleUtil.set_settings(eagle, self.settings)
        EagleUtil.set_grid(eagle)
        
        for layer in self.layers:
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
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        pass
        
class Part (object):
    def __init__ (self, name=None, library=None, deviceset=None, device=None, package=None):
        self.name = name
        self.library = library
        self.deviceset = deviceset
        self.device = device
        
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
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        pass
        
class Device (object):
    def __init__ (self, name=None, technologies=[]):
        self.name = name
        self.technologies = technologies
        
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
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        pass
        
class Segment (object):
    def __init__ (self, pinrefs=[], wires=[]):
        self.pinrefs = pinrefs
        self.wires = wires
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        pass
    
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
        assert et.tag() == "layer"
        layer = Layer(
            number=et.get("number"),
            name=et.get("name"),
            color=et.get("color"),
            fill=et.get("fill"),
            visible=et.get("visible"),
            active=et.get("active")
        )
        
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
    
    
    
    
    
    
    
    
    
    
    
    
    
    