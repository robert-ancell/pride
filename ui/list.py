# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .frame import Frame
from .widget import Widget

class List (Widget):
    def __init__ (self):
        Widget.__init__ (self)
        self.focus_child = None
        self.children = []
        self.set_scale (1.0, 1.0)

    def add_child (self, child, index = -1):
        if index >= 0:
            self.children.insert (child, index)
        else:
            self.children.append (child)

    def focus (self, child):
        self.focus_child = child

    def handle_event (self, event):
        if self.focus_child is None:
            return
        self.focus_child.handle_event (event)

    def render (self, frame):
        visible_children = []
        for child in self.children:
            if child.visible:
                visible_children.append (child)

        # Allocate space for children
        min_height = 0
        total_scales = 0.0
        for child in visible_children:
            (height, _) = child.get_size ()
            min_height += height
            total_scales += child.y_scale
        min_height = min (min_height, frame.height)

        line_offset = 0
        for child in visible_children:
            (height, _) = child.get_size ()
            height += int (child.y_scale * (frame.height - min_height) / total_scales) # FIXME: Handle remaining amount fairly - give integer amounts then remaining based on fractional amounts
            child_frame = Frame (frame.width, height)
            child.render_aligned (child_frame)
            frame.composite (0, line_offset, child_frame)
            if child is self.focus_child:
                frame.cursor = (line_offset + child_frame.cursor[0], child_frame.cursor[1])
            line_offset += height
