

class PartParameter:
    name = None
    type = "str"
    value = None
    key = None

    
    def __init__(self, name, key, type = "str", parse = lambda x:x, value = None, render=lambda x: str(x)):
        self.name = name
        self.type = type
        self.value = value
        self.key = key
        self.parse = parse
        self.render = render
        
    def __str__(self):
        return self.name + " = " + (self.render(self.value) if self.value != None else "*")

