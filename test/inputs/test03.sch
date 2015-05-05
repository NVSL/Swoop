<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE eagle SYSTEM "eagle.dtd">
<eagle version="7.2.0">
  <drawing>
    <settings>
      <setting alwaysvectorfont="no"/>
      <setting verticaltext="up"/>
    </settings>
    <grid distance="0.1" unitdist="inch" unit="inch" style="lines" multiple="1" display="no" altdistance="0.01" altunitdist="inch" altunit="inch"/>
    <layers>
      <layer number="91" name="Top" color="4" fill="1" visible="no" active="no"/>
    </layers>
    <schematic>
      <libraries/>
      <attributes/>
      <variantdefs/>
      <classes>
        <class number="0" name="default" width="0.0" drill="0.0"/>
        <class number="1" name="power" width="0.3048" drill="0.0"/>
      </classes>
      <parts/>
      <sheets>
        <sheet>
          <plain/>
          <instances/>
          <busses/>
          <nets>
            <net name="DTR/RTS" class="0">
              <segment>
                <pinref part="C4" gate="G$1" pin="2"/>
                <pinref part="FTDI" gate="G$1" pin="6"/>
                <wire x1="121.92" y1="149.86" x2="88.9" y2="149.86" width="0.1524" layer="91"/>
              </segment>
            </net>
          </nets>
        </sheet>
      </sheets>
    </schematic>
  </drawing>
</eagle>
