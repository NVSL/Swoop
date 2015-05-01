import Circuits

LED_circuit = Circuits.CircuitPlan() # class represents schematic + library

LED_circuit += Circuits.LED(name="D1") # add one of the default parts to the board; name is used for lookup and becomes the schematic/board reference designator

battery = Circuits.Battery(voltage=3) # some parts take other parameters; name will be assigned some good default automatically
battery.pins["V-"].rename("GND") # parts have pins and those pins have default names that can be changed

LED_circuit += battery # add part to circuit

ground_net = LED_circuit.new_net("GND") # make a new net

for pin in LED_circuit.parts["D1"].pins.values(): # iterator is not the best way to do this but it's cool to be able to do this
    if pin == "C": # equality overload to test pin name with string
        R1 = Circuits.Resistor(name="R1", resistance=470) # make a resistor
        assert R1.resistance == 470, "Attributes should be accessible as members."
        LED_circuit += R1 # and add it to the circuit 
        R1.pins.values()[0].connect( pin )
        
        ground_net += R1.pins.values()[1] # add a pin to net
        LED_circuit.nets["GND"] += battery.pins["GND"] # adding another pin to the net connects the resistor to ground
        
    elif pin == "A":
        pin.connect( battery.pins["V+"] )
        
LED_circuit.export(style="EAGLE", filename="led_test_circuit.sch") # write out as a file
LED_circuit.boardify() # creates a suitable board outline, places the parts, and routes the board 

#LED_circuit.order(provider="4pcb.com", shipping="UPS Ground", ship_to="home") # some day











