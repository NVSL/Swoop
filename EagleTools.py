from HighEagle import EagleFile
from HighEagle import EaglePartVisitor
import HighEagle as HE

class ScanLayersVisitor(EaglePartVisitor):

    """
    Scan the file for all EFPs with a "layer" attribute and collected the names of all layers that are used somewhere in the file.
    """
    def __init__(self, efp):
        EaglePartVisitor.__init__(self,efp)
        self.foundLayers = set()
        self.definedLayers = set()

    def default_pre(self, efp):
        if "layer" in efp.__dict__:
            assert type(efp.layer) == str
            self.foundLayers.add(efp.layer)

    def Layer_pre(self, efp):
        assert type(efp) == HE.Layer
        self.definedLayers.add(efp.name)
        
    def getUsedLayers(self):
        """
        Get a list of used layers
        """
        return list(self.foundLayers)

    def getUnusedLayers(self):
        """
        Get a list of unused layers
        """
        return list(self.definedLayers - self.foundLayers)

    def getDefinedLayers(self):
        """ 
        Get the list of layers declared in the file (i.e., in the <layers>)
        """
        return list(self.definedLayers)

class ScanLibraryReferences(EaglePartVisitor):
    """
    Scan the EF and identify all the library components (Libraries, Symbols, Packages, Devicesets, and Devices) that are referenced in the file.
    """
    
    def __init__(self, efp):
        EaglePartVisitor.__init__(self,efp)
        self.usedEFPs = set()
        
    def Part_pre(self, efp):

        self.usedEFPs.add(efp.get_library())
        self.usedEFPs.add(efp.get_deviceset())
        self.usedEFPs.add(efp.get_device())

        if efp.get_device().get_package():
            self.usedEFPs.add(efp.get_device().get_package())
        
        for i in efp.get_deviceset().get_gates():
            self.usedEFPs.add(i.get_symbol())
    
    def get_referenced_efps(self):
        """
        return a list of all the library components that are used.
        """
        return list(self.usedEFPs)
        

class DumpVisitor(EaglePartVisitor):

    def __init__(self, efp):
        EaglePartVisitor.__init__(self,efp)

    def default_pre(self, efp):
        print "pre " + type(efp).__name__

    def default_post(self, efp):
        print "pre " + type(efp).__name__

def mergeLayers(src, dst, force=False):
    """
    Merge layers from the src eagle file to the dst.  If there is some conflict
    between the two (different names for the same layer number or vice versa),
    then raise an exception (unless force == True)
    """
    for srcLayer in src.get_layers().values():
        for dstLayer in dst.get_layers().values():
            if ((srcLayer.name == dstLayer.name and srcLayer.number != dstLayer.number) or 
                (srcLayer.name != dstLayer.name and srcLayer.number == dstLayer.number)):
                if force:
                    try:
                        src.remove_layer(dstLayer)
                    except:
                        pass
                else:
                    raise HE.HighEagleError("Layer mismatch: " +
                                            src.filename + " <" + str(srcLayer.number) + ", '" + srcLayer.name +"'>; " +
                                            dst.filename +" = <" + str(dstLayer.number) + ", '" + dstLayer.name +"'>;")
        if srcLayer.name not in dst.get_layers():
            dst.add_layer(srcLayer.clone())
        
def normalizeLayers(ef, layers, force=False):
    """
    Clean up layers in a file.  First, remove all unused layers, then merge in the
    layers from layers (typically a file with a standard set of layers).  If
    force == True, overwrite layers in ef with layers.

    """
    for i in ScanLayersVisitor(ef).go().getUnusedLayers():
        #print "removed " + str(i)
        ef.remove_layer(i)
        
    mergeLayers(layers, ef, force)

