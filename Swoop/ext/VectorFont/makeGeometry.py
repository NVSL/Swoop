import sys
import re
import collections

VectorFont = collections.namedtuple("VectorFont", ["base_height", "base_width", "base_kerning", "glyphs"])
Glyph = collections.namedtuple("Glyph", ["width", "lines"])

vectorFont = VectorFont(1,
                        0.667258, #empircal value
                        6445*0.00001*25.4,  #empircal value
                        {})
font = {}
for fname in sys.argv[1:]:
    f = open(fname)
    xrange = [100000,-100000]
    #yrange = [100000,-100000]
    
    lines = []
    for l in f.readlines():
        m = re.match("X(-?)0*(\d+)Y(-?)0*(\d+)D(0.)", l)
        if m is not None:
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
            vectorFont.glyphs[chr(int(fname[:-4]))] = Glyph(xrange[1]-xrange[0], lines)

print("vector_font = {}".format(vectorFont))
