import copy

import EagleUtil

class CircuitPlan (object):
    def __init__ (self):
        self.parts = {}
        
    def __add__ (self, other):
        new = copy.deepcopy(self)
        new += other
        return new
        
    def pins (self):
        pins = []
        for part in self.parts:
            pins += part.pins.values()
            
        return pins
        
    def __iadd__ (self, other):
        if isinstance(other, Component):
            if other.name in self.parts:
                raise ValueError("Adding a second part with the same name is not allowed. Parts: "+self.parts.__str__())    
            self.parts[other.name] = other
            other.circuit = self
        else:
            raise TypeError("Can only add Component type to CircuitPlan type.")
        
        return self
        
    def connect (self, a, b):
        assert isinstance(a, Pin) and isinstance(b, Pin), "Can only connect Pin to Pin, not "+type(a)+" to "+type(b)+"."
        a.net += b.net
        b.net = a.net
        
    def export (self, style="EAGLE", filename="default.sch"):
        if style == "EAGLE":
            sch = EagleUtil.export_to_eagle(self, filename)
        else:
            raise ValueError("Style not supported: "+style)
        
    def boardify (self):
        pass
        
    def order (self, provider, shipping, ship_to):
        raise Exception("You wish.")
    
class Component (object):
    def __init__ (self, circuit=None, name=None):
        self.pins = {}
        self.name = name
        self.circuit = circuit
        
    def __add__ (self, pin):
        new = copy.deepcopy(self)
        new += pin
        return new
        
    def __iadd__ (self, pin):
        if isinstance(pin, Pin):
            self.pins[pin.name] = pin
            pin.component = self
        else:
            raise TypeError("Can only add Pin to Component")
            
        return self
        
class Diode (Component):
    def __init__ (self, name=None):
        Component.__init__(self, name=name)
        self += Pin("A")
        self += Pin("C")
        
class LED (Diode):
    def __init__ (self, name=None):
        Component.__init__(self, name=name)
    
class Resistor (Component):
    def __init__ (self, name=None):
        Component.__init__(self, name=name)
        
class Battery (Component):
    def __init__ (self, name=None, voltage=None):
        Component.__init__(self, name)
        self += Pin("V-")
        self += Pin("V+")
        
class Pin (object):
    def __init__ (self, name=None):
        self.name = name
        self.component = None
        self.net = None
        
    def __add__ (self, other):
        if isinstance(other, Pin):
            self.component.circuit.connect(self, other)
        else:
            raise TypeError("Can only add Pin type to Pin type.")
        
    def __eq__ (self, other):
        if isinstance(other, str):
            return self.name == other
        else:
            return object.__eq__(self, other)
            
            
    def __ne__ (self, other):
        return not (self == other)
        
    def rename (self, name):
        self.name = name
