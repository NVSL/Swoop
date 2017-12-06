import Swoop


brd = Swoop.EagleFile.open("template.brd")


for c in range(32, 127):
    t = brd.clone();
    print("{} {}".format(c, chr(c)))
    s = chr(c)
    if s == "\\":
        s = "\\\\"
        
    t.add_plain_element(Swoop.Text().
                        set_location(0,0).
                        set_size(1).
                        set_ratio(0).
                        set_font("vector").
                        set_layer("tPlace").
                        set_align("top-left").
                        #set_distance(50).
                        set_text(s))
    t.write(str(c)+ ".brd")
