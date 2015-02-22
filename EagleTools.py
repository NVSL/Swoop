from HighEagle import EagleFile
from HighEagle import EaglePartVisitor
import HighEagle as HE

class ScanLayersVisitor(EaglePartVisitor):

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
        return list(self.foundLayers)

    def getUnusedLayers(self):
        return list(self.definedLayers - self.foundLayers)

    def getDefinedLayers(self):
        return list(self.definedLayers)

class DumpVisitor(EaglePartVisitor):

    def __init__(self, efp):
        EaglePartVisitor.__init__(self,efp)

    def default_pre(self, efp):
        print "pre " + type(efp).__name__

    def default_post(self, efp):
        print "pre " + type(efp).__name__

def mergeLayers(src, dst, force=False):
    for srcLayer in src.get_layers().values():
        for dstLayer in dst.get_layers().values():
            if ((srcLayer.name == dstLayer.name and srcLayer.number != dstLayer.number) or 
                (srcLayer.name != dstLayer.name and srcLayer.number == dstLayer.number)):
                if force:
                    src.remove_layer(dstLayer)
                else:
                    raise HighEagleError("Layer mismatch: " +
                                         ef.filename + " <" + str(srcLayer.number) + ", '" + srcLayer.name +"'>; " +
                                         src.filename +" = <" + str(dstLayer.number) + ", '" + dstLayer.name +"'>;")
        if srcLayer.name not in dst.get_layers():
            dst.add_layer(srcLayer.clone())
        
def normalizeLayers(ef, layers, force=False):
    
    for i in ScanLayersVisitor(ef).go().getUnusedLayers():
        #print "removed " + str(i)
        ef.remove_layer(i)
        
    mergeLayers(layers, ef, force)
