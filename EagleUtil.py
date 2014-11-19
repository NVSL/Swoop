import xml.etree.ElementTree as ET

def export_to_eagle (circuit, filename):
    eagle = ET.Element("eagle")
    drawing = ET.SubElement(eagle, "drawing")
    settings = ET.SubElement(drawing, "settings")
    grid = ET.SubElement(drawing, "grid")
    layers = ET.SubElement(drawing, "layers")
    schematic = ET.SubElement(drawing, "schematic")
    libraries = ET.SubElement(schematic, "libraries")
    attributes = ET.SubElement(schematic, "attributes")
    variantdefs = ET.SubElement(schematic, "variantdefs")
    classes = ET.SubElement(schematic, "classes")
    parts = ET.SubElement(schematic, "parts")
    sheets = ET.SubElement(schematic, "sheets")
    
    set_layers_from_file(eagle)
    default_settings(eagle)
    default_class(eagle)
    inch_grid(eagle)
    sheet = add_empty_sheet(eagle)
    
    ET.dump(eagle)
    
    tree = ET.ElementTree(eagle)
    tree.write(filename)
    
def empty_schematic ():
    eagle = ET.Element("eagle")
    drawing = ET.SubElement(eagle, "drawing")
    settings = ET.SubElement(drawing, "settings")
    grid = ET.SubElement(drawing, "grid")
    layers = ET.SubElement(drawing, "layers")
    schematic = ET.SubElement(drawing, "schematic")
    libraries = ET.SubElement(schematic, "libraries")
    attributes = ET.SubElement(schematic, "attributes")
    variantdefs = ET.SubElement(schematic, "variantdefs")
    classes = ET.SubElement(schematic, "classes")
    parts = ET.SubElement(schematic, "parts")
    sheets = ET.SubElement(schematic, "sheets")
    
    return eagle
    
def add_library (root, library):
    root.find("./drawing/libraries").append(library)

def make_empty_library ():
    library = ET.Element("library")
    
    ET.SubElement(library, "description")
    ET.SubElement(library, "packages")
    ET.SubElement(library, "symbols")
    ET.SubElement(library, "devicesets")
    
    return library
    
def make_empty_package ():
    package = ET.Element
    
def set_layers_from_file (root, filename="gtron_layers.xml"):
    layers = ET.parse(filename)
    layers = list(layers.getroot())
    root.find("./drawing/layers").extend(layers)
    
def make_layer (number=None, name=None, color="7", fill="1", visible="yes", active="yes"):
    layer_root = ET.Element("layer")
    layer_root.set("number", number)
    layer_root.set("name", name)
    layer_root.set("color", color)
    layer_root.set("fill", fill)
    layer_root.set("visible", visible)
    layer_root.set("active", active)
    return layer_root
    
def add_layer (root, layer_root):
    assert(isinstance(root, ET.Element))
    assert(isinstance(layer_root, ET.Element))
    assert(layer_root.tag == "layer")
    root.find("./drawing/layers").append(layer_root)
    
def get_default_layers ():
    return ET.fromstring(
        """
        <layers>
        <layer number="1" name="Top" color="4" fill="1" visible="no" active="no"/>
        <layer number="16" name="Bottom" color="1" fill="1" visible="no" active="no"/>
        <layer number="17" name="Pads" color="2" fill="1" visible="no" active="no"/>
        <layer number="18" name="Vias" color="2" fill="1" visible="no" active="no"/>
        <layer number="19" name="Unrouted" color="6" fill="1" visible="no" active="no"/>
        <layer number="20" name="Dimension" color="15" fill="1" visible="no" active="no"/>
        <layer number="21" name="tPlace" color="16" fill="1" visible="no" active="no"/>
        <layer number="22" name="bPlace" color="14" fill="1" visible="no" active="no"/>
        <layer number="23" name="tOrigins" color="15" fill="1" visible="no" active="no"/>
        <layer number="24" name="bOrigins" color="15" fill="1" visible="no" active="no"/>
        <layer number="25" name="tNames" color="7" fill="1" visible="no" active="no"/>
        <layer number="26" name="bNames" color="7" fill="1" visible="no" active="no"/>
        <layer number="27" name="tValues" color="7" fill="1" visible="no" active="no"/>
        <layer number="28" name="bValues" color="7" fill="1" visible="no" active="no"/>
        <layer number="29" name="tStop" color="7" fill="3" visible="no" active="no"/>
        <layer number="30" name="bStop" color="7" fill="6" visible="no" active="no"/>
        <layer number="31" name="tCream" color="7" fill="4" visible="no" active="no"/>
        <layer number="32" name="bCream" color="7" fill="5" visible="no" active="no"/>
        <layer number="33" name="tFinish" color="6" fill="3" visible="no" active="no"/>
        <layer number="34" name="bFinish" color="6" fill="6" visible="no" active="no"/>
        <layer number="35" name="tGlue" color="7" fill="4" visible="no" active="no"/>
        <layer number="36" name="bGlue" color="7" fill="5" visible="no" active="no"/>
        <layer number="37" name="tTest" color="7" fill="1" visible="no" active="no"/>
        <layer number="38" name="bTest" color="7" fill="1" visible="no" active="no"/>
        <layer number="39" name="tKeepout" color="4" fill="11" visible="no" active="no"/>
        <layer number="40" name="bKeepout" color="1" fill="11" visible="no" active="no"/>
        <layer number="41" name="tRestrict" color="4" fill="10" visible="no" active="no"/>
        <layer number="42" name="bRestrict" color="1" fill="10" visible="no" active="no"/>
        <layer number="43" name="vRestrict" color="2" fill="10" visible="no" active="no"/>
        <layer number="44" name="Drills" color="7" fill="1" visible="no" active="no"/>
        <layer number="45" name="Holes" color="7" fill="1" visible="no" active="no"/>
        <layer number="46" name="Milling" color="3" fill="1" visible="no" active="no"/>
        <layer number="47" name="Measures" color="7" fill="1" visible="no" active="no"/>
        <layer number="48" name="Document" color="7" fill="1" visible="no" active="no"/>
        <layer number="49" name="Reference" color="7" fill="1" visible="no" active="no"/>
        <layer number="50" name="dxf" color="7" fill="1" visible="no" active="no"/>
        <layer number="51" name="tDocu" color="7" fill="1" visible="no" active="no"/>
        <layer number="52" name="bDocu" color="7" fill="1" visible="no" active="no"/>
        <layer number="53" name="tGND_GNDA" color="7" fill="9" visible="no" active="no"/>
        <layer number="54" name="bGND_GNDA" color="1" fill="9" visible="no" active="no"/>
        <layer number="56" name="wert" color="7" fill="1" visible="no" active="no"/>
        <layer number="57" name="tCAD" color="7" fill="1" visible="no" active="no"/>
        <layer number="90" name="Modules" color="5" fill="1" visible="yes" active="yes"/>
        <layer number="91" name="Nets" color="2" fill="1" visible="yes" active="yes"/>
        <layer number="92" name="Busses" color="1" fill="1" visible="yes" active="yes"/>
        <layer number="93" name="Pins" color="2" fill="1" visible="no" active="yes"/>
        <layer number="94" name="Symbols" color="4" fill="1" visible="yes" active="yes"/>
        <layer number="95" name="Names" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="96" name="Values" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="97" name="Info" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="98" name="Guide" color="6" fill="1" visible="yes" active="yes"/>
        <layer number="100" name="Muster" color="7" fill="1" visible="no" active="no"/>
        <layer number="101" name="Patch_Top" color="12" fill="4" visible="yes" active="yes"/>
        <layer number="102" name="Vscore" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="103" name="tMap" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="104" name="Name" color="16" fill="1" visible="yes" active="yes"/>
        <layer number="105" name="tPlate" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="106" name="bPlate" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="107" name="Crop" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="108" name="fp8" color="7" fill="1" visible="no" active="no"/>
        <layer number="109" name="fp9" color="7" fill="1" visible="no" active="no"/>
        <layer number="110" name="fp0" color="7" fill="1" visible="no" active="no"/>
        <layer number="111" name="LPC17xx" color="7" fill="1" visible="no" active="no"/>
        <layer number="112" name="tSilk" color="7" fill="1" visible="no" active="no"/>
        <layer number="116" name="Patch_BOT" color="9" fill="4" visible="yes" active="yes"/>
        <layer number="121" name="_tsilk" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="122" name="_bsilk" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="123" name="tTestmark" color="7" fill="1" visible="no" active="no"/>
        <layer number="124" name="bTestmark" color="7" fill="1" visible="no" active="no"/>
        <layer number="125" name="_tNames" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="126" name="_bNames" color="7" fill="1" visible="no" active="no"/>
        <layer number="127" name="_tValues" color="7" fill="1" visible="no" active="no"/>
        <layer number="128" name="_bValues" color="7" fill="1" visible="no" active="no"/>
        <layer number="131" name="tAdjust" color="7" fill="1" visible="no" active="no"/>
        <layer number="132" name="bAdjust" color="7" fill="1" visible="no" active="no"/>
        <layer number="144" name="Drill_legend" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="150" name="tFaceplate" color="11" fill="1" visible="yes" active="yes"/>
        <layer number="151" name="HeatSink" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="152" name="_bDocu" color="7" fill="1" visible="no" active="no"/>
        <layer number="153" name="FabDoc1" color="6" fill="1" visible="no" active="no"/>
        <layer number="154" name="FabDoc2" color="2" fill="1" visible="no" active="no"/>
        <layer number="155" name="FabDoc3" color="7" fill="15" visible="no" active="no"/>
        <layer number="160" name="tMountFaceplate" color="11" fill="1" visible="no" active="yes"/>
        <layer number="161" name="bMountFaceplate" color="11" fill="1" visible="no" active="yes"/>
        <layer number="199" name="Contour" color="7" fill="1" visible="no" active="no"/>
        <layer number="200" name="200bmp" color="1" fill="10" visible="yes" active="yes"/>
        <layer number="201" name="201bmp" color="2" fill="10" visible="yes" active="yes"/>
        <layer number="202" name="202bmp" color="3" fill="10" visible="yes" active="yes"/>
        <layer number="203" name="203bmp" color="4" fill="10" visible="yes" active="yes"/>
        <layer number="204" name="204bmp" color="5" fill="10" visible="yes" active="yes"/>
        <layer number="205" name="205bmp" color="6" fill="10" visible="yes" active="yes"/>
        <layer number="206" name="206bmp" color="7" fill="10" visible="yes" active="yes"/>
        <layer number="207" name="207bmp" color="8" fill="10" visible="yes" active="yes"/>
        <layer number="208" name="208bmp" color="9" fill="10" visible="yes" active="yes"/>
        <layer number="209" name="209bmp" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="210" name="210bmp" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="211" name="211bmp" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="212" name="212bmp" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="213" name="213bmp" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="214" name="214bmp" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="215" name="215bmp" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="216" name="216bmp" color="7" fill="1" visible="yes" active="yes"/>
        <layer number="217" name="217bmp" color="18" fill="1" visible="no" active="no"/>
        <layer number="218" name="218bmp" color="19" fill="1" visible="no" active="no"/>
        <layer number="219" name="219bmp" color="20" fill="1" visible="no" active="no"/>
        <layer number="220" name="220bmp" color="21" fill="1" visible="no" active="no"/>
        <layer number="221" name="221bmp" color="22" fill="1" visible="no" active="no"/>
        <layer number="222" name="222bmp" color="23" fill="1" visible="no" active="no"/>
        <layer number="223" name="223bmp" color="24" fill="1" visible="no" active="no"/>
        <layer number="224" name="224bmp" color="25" fill="1" visible="no" active="no"/>
        <layer number="248" name="Housing" color="7" fill="1" visible="no" active="no"/>
        <layer number="249" name="Edge" color="7" fill="1" visible="no" active="no"/>
        <layer number="250" name="Descript" color="3" fill="1" visible="no" active="no"/>
        <layer number="251" name="SMDround" color="12" fill="11" visible="no" active="no"/>
        <layer number="254" name="cooling" color="7" fill="1" visible="yes" active="yes"/>
        </layers>
        """
    )
    
def get_layers (root):
    if root.tag == "eagle":
        layers = root.findall("./drawing/layers/layer")
        return layers
    else:
        raise NotImplementedError("Don't know how to find layers in "+root.tag+" section.")   
    
def get_grid (root):
    if root.tag == "eagle":
        grid_root = root.find("./drawing/grid")
        return grid_root
    else:
        raise NotImplementedError("Don't know how to find grid in "+root.tag+" section.")
    
    
def get_sheets (root):
    if root.tag == "eagle":
        sheets = root.findall("./drawing/schematic/sheets/sheet")
        return sheets
    else:
        raise NotImplementedError("Don't know how to find sheets in "+root.tag+" section.")
    
    
def get_settings (root):
    if root.tag == "eagle":
        settings = root.findall("./drawing/settings/setting")
        return settings
    else:
        raise NotImplementedError("Don't know how to find settings in "+root.tag+" section.")
    
def get_libraries (root):
    if root.tag == "eagle":
        libraries = root.findall("./drawing/schematic/libraries/library")
        return libraries
    else:
        raise NotImplementedError("Don't know how to find libraries in "+root.tag+" section.")

    
def get_attributes (root):
    return []
    
def get_variantdefs (root):
    return []
    
def get_description (root):
    desc = root.find("./description")
    
    if desc is not None:
        return desc.text
    else:
        return None
    
def get_classes (root):
    if root.tag == "eagle":
        classes = root.findall("./drawing/schematic/classes")
        return classes
    else:
        raise NotImplementedError("Don't know how to find classes in "+root.tag+" section.")

def get_parts (root):
    parts = root.findall("./drawing/schematic/parts/part")
    return parts
    
def get_packages (root):
    if root.tag == "library":
        return root.findall("./packages/package")
    else:
        raise Exception("Don't know how to find packages in section: "+root.tag)
    
def set_settings (root, settings):
    settings_root = root.find("./drawing/settings")
    for setting in settings:
        ET.SubElement(settings_root, "setting").set(setting, settings[setting])
    
def default_settings (root):
    settings = root.find("./drawing/settings")
    ET.SubElement(settings, "setting").set("alwaysvectorfont", "no")
    ET.SubElement(settings, "setting").set("verticaltext", "up")
    
def default_class (root):
    classes = root.find("./drawing/schematic/classes")
    default = ET.SubElement(classes, "class")
    default.set("number", "0")
    default.set("name", "default")
    default.set("width", "0")
    default.set("drill", "0")
    
def set_grid (
    root, 
    distance="0.1", 
    unitdist="inch", 
    unit="inch", 
    style="lines", 
    multiple="1", 
    display="no",
    altdistance="0.01",
    altunitdist="inch",
    altunit="inch"
):
    grid_root = root.find("./drawing/grid")
    grid_root.set("distance", distance)
    grid_root.set("unitdist", unitdist)
    grid_root.set("unit", unit)
    grid_root.set("style", style)
    grid_root.set("multiple", multiple)
    grid_root.set("display", display)
    grid_root.set("altdistance", altdistance)
    grid_root.set("altunitdist", altunitdist)
    grid_root.set("altunit", altunit)
    
    
def add_sheet (root, sheet):
    root.find("./drawing/schematic/sheets").append(sheet)
    
def get_empty_sheet ():
    sheet = ET.Element("sheet")
    
    ET.SubElement(sheet, "plain")
    ET.SubElement(sheet, "instances")
    ET.SubElement(sheet, "busses")
    ET.SubElement(sheet, "nets")
    
    return sheet

def get_symbols (root):
    if root.tag == "library":
        return root.findall("./symbols/symbol")
    else:
        raise NotImplementedError("Don't know how to find symbols in "+root.tag+" section.")

def get_devicesets (root):
    if root.tag == "library":
        return root.findall("./devicesets/deviceset")
    else:
        raise NotImplementedError("Don't know how to find devicesets in "+root.tag+" section.")

def get_pads (root):
    if root.tag == "package":
        return root.findall("pad")
    else:
        raise NotImplementedError("Don't know how to find pads in "+root.tag+" section.")

def get_smds (root):
    if root.tag == "package":
        return root.findall("smd")
    else:
        raise NotImplementedError("Don't know how to find pads in "+root.tag+" section.")

def get_drawing (root):
    drawings = []
    
    drawings += root.findall("./wire")
    drawings += root.findall("./rectangle")
    drawings += root.findall("./text")
    drawings += root.findall("./circle")
    
    return drawings

def get_pins (root):
    if root.tag == "symbol":
        return root.findall("./pin")
    else:
        raise NotImplementedError("Don't know how to find pins in "+root.tag+" section.")

def get_gates (root):
    if root.tag == "deviceset":
        return root.findall("./gates/gate")
    else:
        raise NotImplementedError("Don't know how to find gates in "+root.tag+" section.")

def get_devices (root):
    if root.tag == "deviceset":
        return root.findall("./devices/device")
    else:
        raise NotImplementedError("Don't know how to find device in "+root.tag+" section.")

def get_connects (root):
    if root.tag == "device":
        return root.findall("./connects/connect")
    else:
        raise NotImplementedError("Don't know how to find connects in "+root.tag+" section.")

def get_technologies (root):
    if root.tag == "device":
        return root.findall("./technologies/technology")
    else:
        raise NotImplementedError("Don't know how to find technologies in "+root.tag+" section.")

def get_plain (root):
    if root.tag == "sheet":
        return root.findall("./plain/*")
    else:
        raise NotImplementedError("Don't know how to find plain in "+root.tag+"section.")

def get_instances (root):
    if root.tag == "sheet":
        return root.findall("./instances/instance")
    else:
        raise NotImplementedError("Don't know how to find instances in "+root.tag+"section.")

def get_buses (root):
    if root.tag == "sheet":
        return root.findall("./buses/bus")
    else:
        raise NotImplementedError("Don't know how to find buses in "+root.tag+"section.")

def get_nets (root):
    if root.tag == "sheet":
        return root.findall("./nets/net")
    else:
        raise NotImplementedError("Don't know how to find nets in "+root.tag+"section.")






















































