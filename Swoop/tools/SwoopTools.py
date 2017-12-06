from Swoop.Swoop import EagleFile
import Swoop
import logging as log
from Swoop.tools.CleanupEagle import *

class ScanLayersVisitor(Swoop.EagleFilePartVisitor):
    """A visitor to scan the file for all :class:`EagleFilePart` objects a
    :code:`layer` attribute and collected the names of all layers that are used
    somewhere in the file.

    """
    def __init__(self, efp):
        Swoop.EagleFilePartVisitor.__init__(self,efp)
        self.foundLayers = set()
        self.definedLayers = set()

    def default_pre(self, efp):
        if "layer" in efp.__dict__ and efp.layer is not None:
            assert type(efp.layer) == str
            self.foundLayers.add(efp.layer)

    def Layer_pre(self, efp):
        assert type(efp) == Swoop.Layer
        self.definedLayers.add(efp.name)
        
    def getUsedLayers(self):
        """
        Get a list of the names of layers used in the file.

        :rtype: List of :code:`str`
        """
        return list(self.foundLayers)

    def getUnusedLayers(self):
        """
        Get a list containing the names of unused layers.

        :rtype: List of :code:`str`

        """
        return list(self.definedLayers - self.foundLayers)

    def getDefinedLayers(self):
        """ 
        Get a list of all the layers defined in the file.

        :rtype: List of :code:`str`

        """
        return list(self.definedLayers)


class ScanLibraryReferences(Swoop.EagleFilePartVisitor):
    """A visitor to scan an :class:`EagleFile` object and identify all the library components (Libraries,
    Symbols, Packages, Devicesets, and Devices) that are referenced in the
    file.

    """
    
    def __init__(self, efp):
        Swoop.EagleFilePartVisitor.__init__(self,efp)
        self.usedEFPs = set()
        
    def Part_pre(self, efp):

        self.usedEFPs.add(efp.get_library())
        self.usedEFPs.add(efp.get_deviceset())
        self.usedEFPs.add(efp.get_device())

        if efp.get_device().get_package():
            self.usedEFPs.add(efp.get_device().get_package())
        
        for i in efp.get_deviceset().get_gates():
            self.usedEFPs.add(i.get_symbol())

    def Element_pre(self, efp):
        raise NotImplementedError("Support for scanning board files not implemented yet")

    def get_referenced_efps(self):
        """
        Return a list of all the library components that are used.
    
        :rtype: List of :class:`EagleFilePart`
        """
        return list(self.usedEFPs)
        

class DumpVisitor(Swoop.EagleFilePartVisitor):

    def __init__(self, efp):
        Swoop.EagleFilePartVisitor.__init__(self,efp)

    def default_pre(self, efp):
        print("pre " + type(efp).__name__)

    def default_post(self, efp):
        print("pre " + type(efp).__name__)

def mergeLayers(src, dst, force=False):
    """
    Merge layers from the :class:`EagleFile` :code:`src` into :class:`EagleFile` :code:`dst`.  If there is some conflict
    between the two (different names for the same layer number or vice versa),
    then raise an exception (unless :code:`force == True`)

    :param src: The :class:`EagleFile` to update.
    :param dst:  The :class:`EagleFile` to draw layers from.
    :param force:  If :code:`True` overwrite the layers.  Otherwise, throw an :class:`SwoopError` on conflict.

    """
    for srcLayer in src.get_layers():
        for dstLayer in dst.get_layers():
            if ((srcLayer.name == dstLayer.name and srcLayer.number != dstLayer.number) or 
                (srcLayer.name != dstLayer.name and srcLayer.number == dstLayer.number)):
                if force:
                    try:
                        src.remove_layer(dstLayer)
                    except:
                        pass
                else:
                    raise Swoop.SwoopError("Layer mismatch: " +
                                            str(src.filename) + " <" + str(srcLayer.number) + ", '" + str(srcLayer.name) +"'>; " +
                                            str(dst.filename) +" = <" + str(dstLayer.number) + ", '" + str(dstLayer.name) +"'>;")
        if srcLayer.name not in dst.get_layersByName():
            dst.add_layer(srcLayer.clone())
        
def normalizeLayers(ef, layers, force=False):
    """Clean up layers in a file.  First, remove all unused layers, then merge in
    the layers from :class:`EagleFile` object :code:`layers`.  If :code:`force
    == True`, overwrite layers in :code:`ef` with the layers even if there is a
    conflict.

    :param ef: The :class:`EagleFile` to update.
    :param layers:  The :class:`EagleFile` to draw layers from.
    :param force:  If :code:`True` overwrite the layers.  Otherwise, throw an :class:`SwoopError` on conflict.

    """

    for i in ScanLayersVisitor(ef).go().getUnusedLayers():
        #print "removed " + str(i)
        ef.remove_layer(i)
        
    mergeLayers(layers, ef, force)

def rebuildBoardConnections(sch, brd):
    """
    Update the signals in :code:`brd` to match the nets in :code:`sch`.  This will set up the connections, but won't draw the air wires.  You can use Eagle's :code:`ripup` command to rebuild those.

    :param sch: :class:`SchematicFile` object and source of the connection information.
    :param brd: :class:`BoardFile` destination for then connection information.
    :rtype: :code:`None`
    
    """
    #sheets/*/net.name:
    for name in Swoop.From(sch).get_sheets().get_nets().get_name():
        sig =  brd.get_signal(name)
        if sig is None:
            brd.add_signal(Swoop.Signal().
                           set_name(name).
                           set_airwireshidden(False).
                           set_class("0")) # We need to do something smarter here.
        else:
            sig.clear_contactrefs()

        for pinref in (Swoop.From(sch).
                       get_sheets().
                       get_nets().
                       with_name(name).
                       get_segments().
                       get_pinrefs()):

            if sch.get_part(pinref.part).find_device().get_package() is None:
                continue

            pads = (Swoop.From(sch).
                   get_parts().
                   with_name(pinref.get_part()).
                   find_device().
                   get_connects().
                   with_gate(pinref.gate).
                   with_pin(pinref.pin).
                   get_pads())

            assert pads is not None;
            if pads is None:
                log.warn("Can't find pads for '{}:{}.{}' on net '{}'".format(pinref.get_part(), pinref.gate, pinref.pin, name))

            for pad in pads:
                brd.get_signal(name).add_contactref(Swoop.Contactref().
                                                    set_element(pinref.get_part()).
                                                    set_pad(pad))


def buildBoardFromSchematic(sch, template_brd):
    """
    Create a minimal board from a schematic file.  :code:`template_brd` is modified and returned.
    
    :param sch: the input schematic
    :param brd: a template :class:`BoardFile`
    :returns: A :class:`BoardFile` object that is consistent with the schematic.
    """

    for part in sch.get_parts():
        propagatePartToBoard(part, template_brd)

    rebuildBoardConnections(sch, template_brd)
    return template_brd

def propagatePartToBoard(part, brd):

    """
    Copy :code:`part` to ``brd`` by creating a new :class:`Element` and populating it accordingly.
    If the part already exists, it will be replaced.  Attributes are not displayed by default, but the display layer is set to "Document".
    
    If the library for the part is missing in the board, it will be create.  If the package is missing, it will be copied.  If it exists and the package for the part and the package in the board are not the same, raise an exception.

    .. Note::
       This function doesn't update the board's signals.  You can run :meth:`rebuildBoardConnections` to do that.

    :param part: :class:`Part` object that to propagate.
    :param brd: Destination :class`BoardFile`.
    :rtype: :code:`None`

    """
    if part.find_device().get_package() is None:
        return
    
    if part.find_package() is None:
        raise Swoop.SwoopError("Can't find package for '{}' ({}.{}.{}.{}).".format(part.get_name(), part.get_library(), part.get_deviceset(), part.get_device(), part.get_technology()))

    dst_lib = brd.get_library(part.get_library())

    if dst_lib is None:
        dst_lib = Swoop.Library().set_name(part.get_library())
        brd.add_library(dst_lib)

    #src_lib = part.find_library()
    #assert src_lib is not None, "Missing library '{}' for part '{}'".format(part.get_library(), part.get_name())
    
    dst_package = dst_lib.get_package(part.find_package().get_name())
    if dst_package is None:
        dst_package = part.find_package().clone()
        dst_lib.add_package(dst_package)
    else:
        assert dst_package.is_equal(part.find_package()), "Package from schematic is not the same as package in board"

    # Reverse-engineered logic about setting values in board files.
    if part.find_deviceset().get_uservalue():
        fallback_value = ""
    else:
        fallback_value = part.get_deviceset()+part.get_device()
    
    n =(Swoop.Element().
        set_name(part.get_name()).
        set_library(part.get_library()).
        set_package(part.
                    find_package().
                    get_name()).
        set_value(part.get_value() if part.get_value() is not None else fallback_value).
        set_x(0).
        set_y(0))

    
    for a in part.find_technology().get_attributes():
        n.add_attribute(a.clone().
                        set_display("off").
                        set_layer("Document"))

    for a in part.get_attributes():
        n.add_attribute(a.clone().
                        set_display("off").
                        set_layer("Document"))


    brd.add_element(n)

def updateLibrary(eagleFile, library):
    """
    Add :code:`library` to :code'eagleFile', overwriting it if it's already
    there.  If it's a schematic, it will add the whole library.  For boards, it
    just adds the packages.

    :param eagleFile: A :class:`SchematicFile` or :class:`BoardFile`.
    :param library: The :class:`Library` to add.
    :returns: Nothing

    """
    l = library.get_library().clone()

    if isinstance(eagleFile, Swoop.BoardFile):
        Swoop.From(l).get_library().get_symbols().detach()
        Swoop.From(l).get_library().get_devicesets().detach()

    eagleFile.add_library(l)


def consolidate_libraries_in_schematic(schematic, new_lib_name, lib_names, cleanup=False):
    """Create a new library called :code:`new_lib_name` in :code:`schematic` that the
    information for all the parts from libraries listed in :code:`lib_names`.

    Update the parts to refer to the new libray.  If :code:`remove_libs` is
    :code:`True`, then remove the old libraries from the schematic.

    Warning:  This will make the schematic inconsistent with the board (if one exists).

    :param schematic: A :class:`SchematicFile` object to operate on.
    :param new_lib_name: The name of the new library.
    :param lib_names: An array of library names to remove.
    :param remove_libs: Should we remove the libraries in :code:`lib_names` after consolidation?
    :returns:  The new :code:`Library` object in :code:`schematic'

    """

    part_names = Swoop.From(schematic).get_parts().filtered_by(lambda x: x.get_library() in lib_names).get_name().unique()
    lib = consolidate_parts_in_schematic(schematic, new_lib_name, part_names)

    if cleanup:
        removeDeadEFPs(schematic)

    return lib
                                                        

def copy_deviceset(deviceset, to_lib):
    """Copy :code:`deviceset` and all associated packages and symbols to :code:`to_lib`.  Fail if there are any name conflicts.

    """

    for p in Swoop.From(deviceset).get_devices().find_package():
        to_lib.add_package(p.clone());
    for s in Swoop.From(deviceset).get_gates().find_symbol():
        to_lib.add_symbol(s.clone());
    to_lib.add_deviceset(deviceset.clone())
    

def consolidate_parts_in_schematic(schematic, lib_name, part_names=None, ignore_conflicts=False):
    """
    Create a new library called :code:`lib_name` in :code:`schematic` that the
    information for the parts listed in :code:`part_names`.  Check for
    conflicting names.

    Update the parts to refer to the new libray. 

    Warning:  This will make the schematic inconsistent with the board (if one exists).

    :param schematic: A :class:`SchematicFile` object to operate on.
    :param lib_name: The name of the new library.
    :param part_names: An array of part names (i.e., reference designators).  If :code:`None` then do all the parts.  Defaults to :code:`None`.
    :returns:  Nothing.
    """

    if schematic.get_library(lib_name) is None:
        lib = Swoop.Library().set_name(lib_name)
        schematic.add_library(lib)
    else:
        lib = schematic.get_library(lib_name)

    src_lib = {}

    def check_for_conflicts(name, lib):
        if name in src_lib:
            assert src_lib[name] == lib, "Name '{}' in both {} and {}".format(name, lib, src_lib[name])
        else:
            src_lib[name] = lib
        
    for p in Swoop.From(schematic).get_parts().filtered_by(lambda x: part_names is None or x.get_name() in part_names):
        package = p.find_device().find_package()
        if package is not None:
            if not ignore_conflicts:
                check_for_conflicts(package.get_name(), p.get_library())
        
        for s in Swoop.From(p).find_deviceset().get_gates().find_symbol():
            if not ignore_conflicts:
                check_for_conflicts(s.get_name(), p.get_library())

        if not ignore_conflicts:
            check_for_conflicts(p.find_deviceset().get_name(), p.get_library())

        copy_deviceset(p.find_deviceset(), lib)

        p.set_library(lib_name)
        
    return lib


def quick_bom(schematic):
    """
    Create a dictionary that maps part names to a dictionary contain all the part's attributes in addition to the following extra attributes:

    * :code:`"refdes"`:  The reference designator for the part.
    * :code:`"device"`:  The device name for the part.
    * :code:`"variant"`: The variant name for the part.
    
    :param schematic: The :class:`SchematicFile` to process.
    """
    parts={}

    for p in Swoop.From(schematic).get_parts():
        attrs = p.get_all_attributes()
        attrs["refdes"] = p.get_name()
        attrs["device"] = p.get_deviceset()
        attrs["variant"] = p.get_device()
        parts[p.get_name()] = attrs
    return parts

def rename_part(old, new, schematic=None, board=None):
    """Rename a part in a schematic and the corresponding board, if provided.
    Change the name of the part and update all references to it.
    
    :param schematic: The :class:`SchematicFile` in which to do the renaming
    :param board: The :class:`BoardFile` in which to do the renaming (optional)
    :param old: Old part name.
    :param new: New part name.

    """
    
    if schematic is not None:
        old_part = schematic.get_part(old)
        old_part.set_name(new)
        
        for i in Swoop.From(schematic).get_sheets().get_instances():
            if i.get_part().upper() == old.upper():
                i.set_part(new.upper())
                
        for pinref in Swoop.From(schematic).get_sheets().get_nets().get_segments().get_pinrefs():
            if pinref.get_part().upper() == old.upper():
                pinref.set_part(new.upper())
                        
    if board is not None:
        for e in Swoop.From(board).get_elements():
            if e.get_name().upper() == old.upper():
                e.set_name(new.upper())

        for contact_ref in Swoop.From(board).get_signals().get_contactrefs():
            if contact_ref.get_element().upper() == old.upper():
                contact_ref.set_element(new.upper())

def rationalize_refdes(schematic=None, board=None):
    """
    Reset (and re-number) all reference designators based on prefixes specified in the libraries.  If the library doesn't provide a prefix, use 'U'.
    
    :param schematic: :class:`SchematicFile` to process
    :param board: :class:`BoardFile` to process
    :returns: A map from old part names to new part names.
    """
    prefix_counts = {}
    rename_map = {}
    for p in Swoop.From(schematic).get_parts():
        prefix = p.find_deviceset().get_prefix()
        if prefix is None:
            prefix = "U"

        before = p.get_name()
        after = "{}{}".format(prefix,prefix_counts.setdefault(prefix,1))
        
        rename_map[before] = after
        rename_part(before,
                    after,
                    board=board,schematic=schematic)
        prefix_counts[prefix] += 1
    return rename_map



def create_empty_library_file(template):
    """
    Create an empty :class:`LibraryFile` object with the layers from template.
    """

    lbr = Swoop.LibraryFile()
    for l in template.get_layers():
        lbr.add_layer(l.clone())
    lbr.set_version(template.get_version())

    return lbr

def create_empty_schematic_file(template):
    """
    Create an empty :class:`SchematicFile` object with the layers from template.
    """

    sch = Swoop.SchematicFile()
    for l in template.get_layers():
        sch.add_layer(l.clone())
    sch.set_version(template.get_version())

    return sch

def create_empty_board_file(template):
    """
    Create an empty :class:`BoardFile` object with the layers from template.
    """

    brd = Swoop.BoardFile()
    for l in template.get_layers():
        brd.add_layer(l.clone())
    brd.set_version(template.get_version())

    return brd
    
