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
    root.find("./drawing/layers").extend(layer_root)
    
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
    
def add_empty_sheet (root):
    sheets = root.find("./drawing/schematic/sheets")
    sheet = ET.SubElement(sheets, "sheet")
    
    ET.SubElement(sheet, "plain")
    ET.SubElement(sheet, "instances")
    ET.SubElement(sheet, "busses")
    ET.SubElement(sheet, "nets")
    
    return sheet