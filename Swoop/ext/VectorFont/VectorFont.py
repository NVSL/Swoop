import sys
import re
from .VectorFontTypes import *

def main():
    
    _vectorFont = VectorFont(base_height=1,
                             base_width=2627*0.00001*25.4, # empircal value. 
                             base_kerning=998*0.00001*25.4,  #empircal value
                             glyphs={})

    for fname in sys.argv[1:]:
        f = open(fname)
        xrange = [100000,-100000]
        #yrange = [100000,-100000]

        lines = []
        foundart = False
        for l in f.readlines():
            m = re.match("X(-?)0*(\d+)Y(-?)0*(\d+)D(0.)", l)
            if m is not None:
                foundart = True
                if m.group(5) == "02":
                    lines.append([])

                xsign = 1 if m.group(1) is "" else -1
                ysign = 1 if m.group(3) is "" else -1

                x = float(m.group(2)) * 0.00001 * 25.4 * xsign
                y = float(m.group(4)) * 0.00001 * 25.4 * ysign

                xrange = [min(xrange[0], x),max(xrange[1], x)]
                #yrange = [min(yrange[0], y),max(yrange[0], y)]

                lines[-1].append((x,y))

                #    print lines
                #print fname, xrange[1]-xrange[0]
        if foundart:
            _vectorFont.glyphs[chr(int(fname[:-4]))] = Glyph(xrange[1]-xrange[0], lines)
        else:
            # This is just for ' '
            _vectorFont.glyphs[chr(int(fname[:-4]))] = Glyph(_vectorFont.base_width, [])
            
    f = open("VectorFontData.py", "w")
    f.write("""from VectorFontTypes import *
vectorFont = {}""".format(_vectorFont))
    f.close()

if __name__ == "__main__":
    main()
    
from .VectorFontData import vectorFont
