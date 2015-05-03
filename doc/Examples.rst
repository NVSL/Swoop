Examples
========

Here are some short examples using Swoop.

Extract the Netlist From a Schematic
------------------------------------

.. code-block:: python

   sch = Swoop.EagleFile.from_file("foo.sch")
   for n in (Swoop.From(sch).  
             get_sheets().   # get all the sheets
             get_nets().     # get all the nets in the sheets
             get_name().     # get all the names of the nets
             unique().       # remove duplicates 
             sort()):        # sort them
      print n + " : " + " ".join(Swoop.From(s).
                                 get_sheets().    # get all the sheets
                                 get_net(n).      # get all the nets with name n
                                 get_segments().  # get all their segments
                                 get_pinrefs().   # get all their pin references  
                                 map(lambda x: str(x.get_part())+ "." + str(x.get_pin())). # combine part name and pin name
                                 sort())          # sort the result.

Will yield something like this::

    D5 : JP4.7 U1.PD5(T1)
    D6 : JP4.6 U1.PD6(AIN0)
    D7 : R5.1 U1.PD7(AIN1)
    D8 : JP4.5 U1.PB0(ICP)
    D9 : JP3.1 U1.PB1(OC1A)
    DTR/RTS : C4.2 FTDI.6
    GND : C1.2 C1A.2 C1B.2 C3.2 C5.2 D3.C D4.C FTDI.1 FTDI.2 GND10.GND GND11.GND GND13.GND GND14.GND GND15.GND GND16.GND GND17.GND GND3.GND GND4.GND GND9.GND J1.2 J2.2 JP1.GND JP4.2 LED1.C LED2.C R1.1 R1A.1 SW1.1 SW1.4 SW1.5 U1.GND U1.GND@1 U1.GND@2 U2.GND U2A.GND U2B.GND Y1.GND

Listing All Drill Sizes Used in a Board
---------------------------------------

.. code-block:: python

    b = Swoop.EagleFile.from_file("foo.brd")
    print (Swoop.From(b).
           get_plain_elements().   # Get the Lines, holes, arcs, polygons, etc. not attached to any package
           with_type(Swoop.Hole).  # We just want the holes.
           add(Swoop.From(b).      # Add some more items to this group of EFPs
               get_elements().     # These are the electrical components
               find_package().     # Grab the package they refer to
               get_pads()).        # get all the pads (i.e., through-hole pins)
           get_drill().            # get the drill attributes for the holes and pads
           sort().                 # sort them
           unique().               # remove duplicates
           unpack())               # get values as python list.

Will yield something like this::

    [1.0, 0.8, 1.1, 1.3, 0.73, 0.7, 1.06]
    

    
