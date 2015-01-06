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

class HighEagle (object):
    def from_et ():
        raise NotImplementedError()
    
    def get_et ():
        raise NotImplementedError()
    
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
        assert len(parts) > 0
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
            new_layer = Layer.from_et(layer)
            sch.layers[new_layer.number] = new_layer
            
        assert len(sch.layers) > 0, "No layers in schematic."
        
        for library in libraries:
            print library
            new_lib = Library.from_et(library)
            sch.libraries[new_lib.name] = new_lib
            
        for attribute in attributes:
            pass
            
        for variantdef in variantdefs:
            pass
            
        for net_class in classes:
            print net_class
            new_class = NetClass.from_et(net_class)
            sch.classes[new_class.name] = new_class
            
        for part in parts:
            print part
            new_part = Part.from_et(part)
            sch.parts[new_part.name] = new_part
            
        assert len(sch.parts) > 0
            
        for sheet in sheets:
            print sheet
            new_sheet = Sheet.from_et(sheet)
            sch.sheets.append(new_sheet)
        
        return sch
        
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
        
        print
        print
        print
        print
        
        eagle = EagleUtil.make_eagle()
        EagleUtil.set_settings(eagle, self.settings)
        EagleUtil.set_grid(eagle)
        
        for layer in self.layers.values():
            EagleUtil.add_layer(eagle, layer.get_et())

        for library in self.libraries.values():
            EagleUtil.add_library(eagle, library.get_et())
            
            
        for attribute in self.attributes:
            pass
            
        for varientdef in self.variantdefs:
            pass
            
        ET.dump(eagle) 
            
        print
        print "Adding net classes"
        
        for net_class in self.classes.values():
            EagleUtil.add_class(eagle, net_class.get_et())
            
        ET.dump(eagle) 
        
        print
        print "Adding parts"
        for part in self.parts.values():
            EagleUtil.add_part(eagle, part.get_et())
            
        ET.dump(eagle) 
            
        print   
        print "Adding sheets"
        for i, sheet in enumerate(self.sheets):
            EagleUtil.add_sheet(eagle, sheet.get_et())
            print "Sheet", i
            #ET.dump(eagle) 
        if len(self.sheets) == 0:
            EagleUtil.add_sheet(eagle, EagleUtil.get_empty_sheet())
            
        ET.dump(eagle)    
            
        return eagle
        
class Pin (object):
    """
    EAGLE pin tag.
    This is a connectible pin on a circuit Symbol. It maps to a Pad or SMD on a Package.
    """
    
    def __init__ (self, name=None, x=None, y=None, visible=None, length=None, direction=None, swaplevel=None, rot=None):
        assert name is not None
        self.name = name
        self.x = x
        self.y = y
        self.visible = visible
        self.length = length
        self.direction = direction
        self.swaplevel = swaplevel
        self.rot = rot
        
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
        
class Library (object):
    def __init__ (self, name=None, description="", packages=None, symbols=None, devicesets=None):
        self.name = name
        if packages is None: packages = {}
        if symbols is None: symbols = {}
        if devicesets is None: devicesets = {}
        
        self.description = description
        self.packages = packages
        self.symbols = symbols
        self.devicesets = devicesets
        
    def load_from_file (self, filename):
        """
        Overwrites the current Library with a new one loaded from the specified file name.
        """
        raise NotImplementedError()
        
    def load_from_file (self, filename):
        """
        Loads a Library from an EAGLE .lbr file.
        """
        raise NotImplementedError()
        
    @classmethod
    def from_et (cls, library_root):
        assert library_root.tag == "library"
        
        lib = cls(name=library_root.get("name"))
        print "Loading library:", lib.name
        lib.description = EagleUtil.get_description(library_root)
        
        packages = EagleUtil.get_packages(library_root)
        symbols = EagleUtil.get_symbols(library_root)
        devicesets = EagleUtil.get_devicesets(library_root)
        
        lib.packages = {}
        for package in packages:
            new_package = Package.from_et(package)
            assert new_package.name not in lib.packages, "Cannot have duplicate package names: "+new_package.name
            lib.packages[new_package.name] = new_package
            
        lib.symbols = {}
        for symbol in symbols:
            new_symbol = Symbol.from_et(symbol)
            assert new_symbol.name not in lib.symbols, "Cannot have duplicate symbol names: "+new_symbol.name
            lib.symbols[new_symbol.name] = new_symbol
            
        lib.devicesets = {}
        for deviceset in devicesets:
            new_deviceset = DeviceSet.from_et(deviceset)
            assert new_deviceset.name not in lib.devicesets, "Cannot have duplicate devicesets names: "+new_deviceset.name
            lib.devicesets[new_deviceset.name] = new_deviceset
            
            
        assert lib is not None
        return lib
        
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
        
        
class Package (object):
    def __init__ (self, name=None, contacts=None, drawings=None):
        self.name = name
        
        if contacts is None: contacts = {}
        if drawings is None: drawings = []
        
        self.drawings = drawings
        self.contacts = contacts
        
    def __str__ (self):
        string = ""
        for key in self.__dict__:
            string += key+": "+(self.__dict__[key].__str__())+"\n"
        return string
        
    @staticmethod
    def from_et (package_root):
        new_package = Package()
        new_package.name = None
        new_package.contacts = {}
        new_package.drawing = []
        
        new_package.name = package_root.get("name")
        pads = EagleUtil.get_pads(package_root)
        smds = EagleUtil.get_smds(package_root)
        drawings = EagleUtil.get_drawing(package_root)
        
        for pad in pads:
            new_pad = Pad.from_et(pad)
            assert new_pad.name not in new_package.contacts, "Cannot add pad with duplicate name: "+new_pad.name
            new_package.contacts[new_pad.name] = new_pad
        
        for smd in smds:
            new_smd = SMD.from_et(smd)
            assert new_smd.name not in new_package.contacts, "Cannot add smd with duplicate name: "+new_smd.name
            new_package.contacts[new_smd.name] = new_smd
            
        for drawing in drawings:
            new_drawing = Drawing.from_et(drawing)
            new_package.drawings.append(new_drawing)
        
        return new_package
        
    def get_et (self):
        #assert len(self.drawings) > 0, self.name # not really needed I guess, might just be pads for the package
        return EagleUtil.make_package(
            name=self.name, 
            drawings=[drawing.get_et() for drawing in self.drawings], 
            contacts=[contact.get_et() for contact in self.contacts.values()]
        )
    
class Pad (object):
    """
    EAGLE pad tag.
    This is a through-hole contact in a Package that gets mapped to a Pin on a Gate.
    """
  
    def __init__ (self, name=None, x=None, y=None, drill=None, diameter=None, shape=None, rot=None):
        self.name = name
        self.x = x
        self.y = y
        self.drill = drill
        self.diameter = diameter
        self.shape = shape
        self.rot = rot
    
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
        
class Rectangle (object):
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
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.layer = layer
        
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
        
class Text (object):
    """
    EAGLE text tag.
    This is used to draw text on the schematic or board.
    """
    def __init__ (self, x=None, y=None, size=None, layer=None, text=None):
        self.x = x
        self.y = y
        self.size = size
        self.layer = layer
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
        
class Circle (object):
    """
    EAGLE circle tag.
    This is used to draw a circle on the schematic or board.
    """
    def __init__ (self, x=None, y=None, radius=None, width=None, layer=None):
        self.x = x
        self.y = y
        self.radius = radius
        self.width = width
        self.layer = layer

        
    @staticmethod
    def from_et (circle_root):
        assert circle_root.tag == "circle"
        return Circle(
            x=circle_root.get("x"),
            y=circle_root.get("y"),
            radius=circle_root.get("radius"),
            width=circle_root.get("width"),
            layer=circle_root.get("layer")
        )
        
    def get_et (self):
        return EagleUtil.make_circle(
            x=self.x,
            y=self.y,
            radius=self.radius,
            width=self.width,
            layer=self.layer
        )
        
class Drawing (object):
    """
    EAGLE drawing tag.
    This is an abstract tag that is used for wire, rectangle, circle, etc.
    """
    
    @staticmethod
    def from_et (drawing_root):
        if drawing_root.tag == "wire":
            return Wire.from_et(drawing_root)
        elif drawing_root.tag == "circle":
            return Circle.from_et(drawing_root)
        elif drawing_root.tag == "rectangle":
            return Rectangle.from_et(drawing_root)
        elif drawing_root.tag == "text":
            return Text.from_et(drawing_root)
        else:
            raise Exception("Don't know how to parse "+drawing_root.tag+" tag as a drawing tag.")
        
class SMD (object):
    """
    EAGLE smd tag.
    This is a smd contact in a Package that gets mapped to a Pin on a Gate.
    """
  
    def __init__ (self, name=None, x=None, y=None, dx=None, dy=None, layer=None, rot=None):
        self.name = name
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.layer = layer
        self.rot = rot
    
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
               
class Symbol (object):
    """
    EAGLE symbol section.
    This section holds circuit diagram symbols that can be used as gates for Devices and Parts.
    """
    
    def __init__ (self, name=None, drawings=None, pins=None):
        self.name = name
        
        if drawings is None: drawings = []
        if pins is None: pins = {}
        
        self.drawings = drawings
        self.pins = pins
    
    @classmethod
    def from_et (cls, symbol_root):
        assert symbol_root.tag == "symbol"
        
        symbol = cls()
        symbol.name = symbol_root.get("name")
        
        drawings = EagleUtil.get_drawing(symbol_root)
        for drawing in drawings:
            new_drawing = Drawing.from_et(drawing)
            symbol.drawings.append(new_drawing)
            
        pins = EagleUtil.get_pins(symbol_root)
        for pin in pins:
            new_pin = Pin.from_et(pin)
            symbol.pins[new_pin.name] = new_pin   

        return symbol
        
    def get_et (self):
        return EagleUtil.make_symbol(
            name=self.name,
            drawings=[drawing.get_et() for drawing in self.drawings],
            pins=[pin.get_et() for pin in self.pins.values()]
        )
    
class Part (object):
    def __init__ (self, name=None, library=None, deviceset=None, device=None, package=None, value=None):
        self.name = name
        self.library = library
        self.deviceset = deviceset
        self.device = device
        self.package = package
        self.value = value
        
    @staticmethod
    def from_et (root):
        name = root.get("name")
        library = root.get("library")
        deviceset = root.get("deviceset")
        device = root.get("device")
        package = root.get("package")
        value = root.get("value")
        
        return Part(name=name, library=library, deviceset=deviceset, device=device, package=package, value=value)
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        return EagleUtil.make_part(
            name=self.name,
            deviceset=self.deviceset,
            library=self.library,
            device=self.device,
            value=self.value
        )
       
        
class DeviceSet (object):
    def __init__ (self, name=None, prefix=None, devices=None, description="", gates=None):
    
        if devices is None: devices = {}
        if gates is None: gates = {}
    
        self.name = name
        self.prefix = prefix
        self.description = description
        self.gates = gates
        self.devices = devices
        
    @classmethod
    def from_et (cls, deviceset_root):
        deviceset = cls(name=deviceset_root.get("name"))
        deviceset.description = EagleUtil.get_description(deviceset_root)
        
        gates = EagleUtil.get_gates(deviceset_root)
        devices = EagleUtil.get_devices(deviceset_root)
        
        for gate in gates:
            new_gate = Gate.from_et(gate)
            name = new_gate.name
            deviceset.gates[name] = new_gate
            
        for device in devices:
            new_device = Device.from_et(device)
            name = new_device.name
            deviceset.devices[name] = new_device
        
        return deviceset
        
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
        
class Gate (object):
    """
    EAGLE Gate.    
    This is a subsection of DeviceSet that specifies the schematic symbol for all Devices in the DeviceSet.
    """
    
    def __init__ (self, name=None, symbol=None, x=0, y=0):
        self.name = name
        self.symbol = symbol
        self.x = x
        self.y = y
        
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
        
        
class Connect (object):
    """
    EAGLE connect tag.
    This maps a Gate's Pin to a Package's Pad or SMD. Subsection of Device.
    """
    
    def __init__ (self, gate=None, pin=None, pad=None):
        self.gate = gate
        self.pin = pin
        self.pad = pad
        
    @classmethod
    def from_et (cls, connect_root):
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
        
class Device (object):
    def __init__ (self, name=None, package=None, connects=None, technologies=None):
    
        if connects is None: connects = []
        if technologies is None: technologies = {}
        self.name = name
        self.package = package
        self.connects = connects
        self.technologies = technologies
        
    @classmethod
    def from_et (cls, device_root):
        assert device_root.tag == "device"
        device = cls()
        
        device.name = device_root.get("name")
        device.package = device_root.get("package")
        
        connects = EagleUtil.get_connects(device_root)
        for connect in connects:
            new_connect = Connect.from_et(connect)
            device.connects.append(new_connect)
            
        
        technologies = EagleUtil.get_technologies(device_root)
        for technology in technologies:
            new_technology = Technology.from_et(technology)
            name = new_technology.name
            device.technologies[name] = new_technology
                
                
        
        return device
        
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
        
class Technology (object):
    """
    EAGLE Technology section.
    This is a subsection of Device.
    """
    
    def __init__ (self, name=None, attributes=None):
        if attributes is None: attributes = {}
        self.attributes = attributes
        self.name = name
        
    @classmethod
    def from_et (cls, technology_root):
        tech = cls()
        tech.name = technology_root.get("name")
        attributes = EagleUtil.get_attributes(technology_root)
        
        for attribute in attributes:
            tech.attributes[attribute.get("name")] = attribute.get("value")
 
        return tech
        
    def get_et (self):
        return EagleUtil.make_technology(name=self.name, attributes=self.attributes)
        
class Attribute (object):
    """
    EAGLE Attribute section.
    This defines the attributes of an EAGLE Technology section.
    There is also an attributes section in the Schematic section but I've never seen this have anything in there.
    """
    
    def __init__ (self, name=None, value=None, constant=None):
        self.name = name
        self.value = value
        self.constant = constant
        
    @staticmethod
    def from_et (attribute_root):
        assert attribute_root.tag == "attribute"
        attribute = Attribute(
            name=attribute.get("name"),
            value=attribute.get("value"),
            constant=attribute.get("constant")
        )
        
    def get_et (self):
        return EagleUtil.make_attribute(
            name=self.name,
            value=self.value,
            constant=self.constant
        )
        
        
class Sheet (object):
    def __init__ (self, plain=None, instances=None, busses=None, nets=None):
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
            pass #process into drawing types
        sheet.plain = plain
        
        instances = EagleUtil.get_instances(sheet_root)
        for instance in instances:
            new_instance = Instance.from_et(instance)
            sheet.instances.append(new_instance)
            
        busses = EagleUtil.get_buses(sheet_root)
        sheet.busses = busses
        
        nets = EagleUtil.get_nets(sheet_root)
        for net in nets:
            new_net = Net.from_et(net)
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
            
        
class Net (object):
    def __init__ (self, name=None, net_class="0", segments=None):
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
        
class Label (object):
    def __init__ (self, x=None, y=None, size=None, layer=None):
        self.x = x
        self.y = y
        self.size = size
        self.layer = layer
        
    @staticmethod
    def from_et (segment_root):
        assert segment_root.tag == "label"
        label = Label()
        label.x = segment_root.get("x")
        label.y = segment_root.get("y")
        label.size = segment_root.get("size")
        label.layer = segment_root.get("layer")
        return label
        
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
        
class Segment (object):
    def __init__ (self, pinrefs=None, portrefs=None, wires=None, junctions=None, labels=None):
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
        
        for wire in wires:
            new_wire = Wire.from_et(wire)
            segment.wires.append(new_wire)
            
        for pinref in pinrefs:
            #ET.dump(pinref)
            new_pinref = PinRef.from_et(pinref)
            segment.pinrefs.append(new_pinref)
            
        for label in labels:
            new_label = Label.from_et(label)
            segment.labels.append(new_label)
            
        return segment
        
    def get_et (self):
        """
        Returns the ElementTree.Element xml representation.
        """
        print "Getting et for segment", self.wires, self.pinrefs, self.labels
        return EagleUtil.make_segment(
            wires=[wire.get_et() for wire in self.wires],
            pinrefs=[pinref.get_et() for pinref in self.pinrefs],
            labels=[label.get_et() for label in self.labels]
        )
        
class Wire (object):
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
        layer=None
    ):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.width = width
        self.layer = layer
        
    @staticmethod
    def from_et (wire_root):
        assert wire_root.tag == "wire"
        return Wire(
            x1=wire_root.get("x1"),
            x2=wire_root.get("x2"),
            y1=wire_root.get("y1"),
            y2=wire_root.get("y2"),
            width=wire_root.get("width"),
            layer=wire_root.get("layer")
        )
        
    def get_et (self):
        return EagleUtil.make_wire(
            x1=self.x1,
            x2=self.x2,
            y1=self.y1,
            y2=self.y2,
            width=self.width,
            layer=self.layer
        )

        
class PinRef (object):
    """
    EAGLE pinref tag.
    This is used in Net Segment to show that a Part's pin is connected to the Net."
    """
    
    
    def __init__ (self, part=None, gate=None, pin=None):
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
    
class Instance (object):
    def __init__ (self, gate=None, part=None, x=None, y=None, rot=None):
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
    
    
    
    
    
    
    
    
    
    