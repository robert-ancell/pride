# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .widget import Widget

class Label (Widget):
    def __init__ (self, text, background = '#000000'):
        Widget.__init__ (self)
        self.text = text
        self.background = background

    def get_size (self):
        max_width = 0
        lines = self.text.split ('\n')
        for line in lines:
            max_width = max (max_width, len (line))
        return (max_width, len (lines))

    def render (self, frame):
        # FIXME: alignment, multi-line
        frame.render_text (0, 0, self.text, background = self.background)
