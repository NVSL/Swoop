import Circuits

LED_circuit = Circuits.CircuitPlan() # class represents schematic + library

LED_circuit += Circuits.LED(name="D1") # add one of the default parts to the board; name is used for lookup and becomes the schematic/board reference designator

battery = Circuits.Battery(voltage=3) # some parts take other parameters; name will be assigned some good default automatically
battery.pins["V-"].rename("GND") # parts have pins and those pins have default names that can be changed
# I don't want to have something like battery.negative_pin because you could already do negative_pin = battery.pins["V-"]
# it also allows string names that could be used as net names in schematic/board
# also then you can iterate over the pins and use other built-in tools if they are at dict natively

LED_circuit += battery # add part to circuit

for pin in LED_circuit.parts["D1"].pins.values(): # iterator is not the best way to do this but it's cool to be able to do this
    if pin == "C": # equality overload to test pin name with string
        R1 = Circuits.Resistor(name="R1", resistance=470) # make a resistor
        LED_circuit += R1 # and add it to the circuit 
        R1.pins.values()[0] + pin # we don't add directly because we want our own reference; more on this syntax later
        
        ground_net += R1.pins.values()[1] # add a pin to net
        ground_net += battery.pins["GND"] # adding another pin to the net connects the resistor to ground
        
    elif pin == "A":
        pin + battery.pins["V+"] # this is a weird syntax but it's cool; really this operation is the heart of circuits-by-code
        # this expression will return a net but we don't need a reference to it
        # if we need a ref to the net we can get it with pin.net
        # the addition creates a net in the circuit
        # you should never create nets with Circuits.Net
        # maybe the coder shouldn't even know that nets exist and use pin.connected_pins to get the connected pins
        # there still has to be something like pin.net_name = "GND" that will assign net_name on all connected pins
        #
        # there is another issue this kind of assignment
        # addition changes the pins, their nets, and the whole circuit
        # it's not really addition, just a convenient operator to overload
        # the alternative is pin.net += battery.pins["V+"] or pin.connect(battery.pins["V+"])
        # I like the straight addition because it looks better to me, but it could be confusing
        
LED_circuit.export(style="EAGLE", filename="led_test_circuit.sch") # write out as a file
LED_circuit.boardify() # creates a suitable board outline, places the parts, and routes the board 
#LED_circuit.order(provider="4pcb.com", shipping="UPS Ground", ship_to="home") # some day











