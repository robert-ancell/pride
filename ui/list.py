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
        n_unallocated = 0
        n_remaining = frame.height
        child_heights = {}
        for child in visible_children:
            size = child.get_size ()
            if size[0] == 0:
                n_unallocated += 1
            child_heights[child] = size[0]
            n_remaining -= size[0]

        # Divide remaining space between children
        if n_unallocated != 0 and n_remaining > 0:
            # FIXME: Use per widget weighting 0.0 - 1.0
            height_per_child = n_remaining // n_unallocated
            extra = n_remaining - height_per_child * n_unallocated
            for child in visible_children:
                if child_heights[child] == 0:
                    child_heights[child] = height_per_child
                    if extra > 0:
                        child_heights[child] += 1
                        extra -= 1

        line_offset = 0
        for child in visible_children:
            height = child_heights[child]
            child_frame = Frame (frame.width, height)
            child.render (child_frame)
            frame.composite (0, line_offset, child_frame)
            if child is self.focus_child:
                frame.cursor = (line_offset + child_frame.cursor[0], child_frame.cursor[1])
            line_offset += height
