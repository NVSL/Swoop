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
      <layer number="1" name="Top" color="4" fill="1" visible="no" active="no"/>
    </layers>
    <schematic>
      <libraries>
        <library name="PickerDesign">
          <packages/>
          <symbols>
            <symbol name="GENERIC-RESISTOR_">
              <pin name="1" x="-5.08" y="0.0" visible="off" length="short" direction="pas" function="none" swaplevel="1"/>
              <pin name="2" x="5.08" y="0.0" visible="off" length="short" direction="pas" function="none" swaplevel="1" rot="R180"/>
            </symbol>
          </symbols>
          <devicesets>
            <deviceset name="GENERIC-RESISTOR_">
              <description/>
              <gates>
                <gate name="G$1" symbol="GENERIC-RESISTOR_" x="0.0" y="0.0"/>
              </gates>
              <devices>
                <device name="">
                  <technologies>
                    <technology name="">
                      <attribute name="SIZE" value="" constant="no"/>
                    </technology>
                  </technologies>
                </device>
              </devices>
            </deviceset>
          </devicesets>
        </library>
      </libraries>
      <attributes/>
      <variantdefs/>
      <parts>
        <part name="R3_3" library="PickerDesign" deviceset="GENERIC-RESISTOR_" device="" value="160 +/- 10%"/>
      </parts>
      <sheets>
        <sheet>
          <plain/>
          <instances>
            <instance part="R3_3" gate="G$1" x="81.28" y="48.26"/>
          </instances>
          <busses/>
          <nets/>
        </sheet>
      </sheets>
    </schematic>
  </drawing>
</eagle>
