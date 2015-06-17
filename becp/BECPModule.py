import Swoop.Swoop as swp

class BECPModule (object):
    def __init__ (self):
        self.swoop_sch = None
        self.parts = None
        self.code_string = None
        
    def load_from_file (file_name):
        self.load_swoop_sch(swp.EagleFile.from_file(file_name))
        
    def load_swoop_sch (swoop_sch):
        self.swoop_sch = swoop_sch
        
        self.parts = {}
        for p in swp.From(self.swoop_sch).get_parts():
            self.parts[p.get_name()] = p
            
        self.code_string = ""
        for code in swp.From(self.swoop_sch).get_sheets().get_plain_elements().with_type(swp.Text):
            if code.layer == "Code":
                print "Found some code"
                print code.text
                print
                self.code_string += code.text + "\n"
    
    def get_pin (self, part_ref, pin_name):
        
        
            
    def connect_nets (self, net_name_1, net_name_2):
        self.rename_net(net_name_1, net_name_2)
        
    def connect_pin (self, part, pin, net):
        
                
    def rename_net (self, old_name, new_name):
        for n in swp.From(self.swoop_sch).get_sheets().get_nets():
            if n.get_name() == old_name:
                n.set_name(new_name)
                
    def new_net (self, new_net_name, net_class = 0, sheet_number = 0):
        if new_net_name in swp.From(self.swoop_sch).get_sheets().get_nets().get_name():
            raise Warning("Could not make new net with name "+new_net_name+" because there is already a net with that name.")
            return
        else:
            new_net = Swoop.Net()
            new_net.set_name(new_net_name)
            new_net.set_netclass(netclass)
            self.swoop_sch.get_sheets()[sheet_number].add_net(new_net)
        
                
    def rename_part (self, old_name, new_name):
        if new_name in self.parts:
            raise Warning("Could not rename part "+old_name+" to "+new_name+" because that name is already in use.")
            return
        elif old_name not in self.parts:
            raise Warning("Could not rename part "+old_name+" to "+new_name+" because no part named "+old_name+".")
            return
        else:
            self.parts[new_name] = self.parts.pop(old_name, None)
            self.parts[new_name].set_name(new_name)
            assert (self.parts[new_name] is not None)
            
            for i in swp.From(self.swoop_sch).get_sheets().get_instances():
                if i.get_part() == old_name:
                    i.set_part(new_name)
                    
            for pr in swp.From(self.swoop_sch).get_sheets().get_nets().get_segments().get_pinrefs():
                if pr.get_part() == old_name:
                    pr.set_part(new_name)
        
    def process (self):
        pass
        
    def save (self, filename):
        self.swoop_sch.get_et().getroottree().write(filename)
