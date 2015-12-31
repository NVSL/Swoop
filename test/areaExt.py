
class Rectangle:
    def __init__(self):
        pass
    def get_area(self):
        return abs((self.get_x2()-self.get_x1()) * (self.get_y1()-self.get_y2()))



class Circle:
    def __init__(self):
        pass
    def get_area(self):
        return math.pi * (self.get_radius()**2)


