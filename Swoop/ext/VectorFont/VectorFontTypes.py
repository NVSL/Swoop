import collections

VectorFont = collections.namedtuple("VectorFont", ["base_height", "base_width", "base_kerning", "glyphs"])
Glyph = collections.namedtuple("Glyph", ["width", "lines"])
