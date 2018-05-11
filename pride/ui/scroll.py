# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

import math

from .widget import Widget

class Scroll (Widget):
    def __init__ (self):
        Widget.__init__ (self)
        self.start = 0
        self.end = 1
        self.set_scale (0.0, 1.0)

    def set_position (self, start, end):
        self.start = max (start, 0.0)
        self.end = min (end, 1.0)

    def get_size (self):
        return (0, 1)

    def render (self, frame):
        frame.clear ()
        start = frame.height * self.start
        end = frame.height * self.end
        y = math.floor (start)
        start_fraction = int ((math.ceil (start) - start) * 8 + 0.5)
        height = math.ceil (end) - y
        end_fraction = int ((end - math.floor (end)) * 8 + 0.5)
        frame.render_vertical_bar (0, y, height, start_fraction, end_fraction)
