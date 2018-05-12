# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .container import Container
from .frame import Frame
from .widget import Widget

class Grid (Container):
    def __init__ (self):
        Container.__init__ (self)
        self.focus_child = None
        self.children = {}
        self.set_scale (1.0, 1.0)

    def add_child (self, child, x, y):
        assert (isinstance (child, Widget))
        self.children[(x, y)] = child

    def append_row (self, child):
        assert (isinstance (child, Widget))
        child_y = 0
        for (_, y) in self.children:
            if y >= child_y:
                child_y = y + 1
        self.add_child (child, 0, child_y)

    def append_column (self, child):
        assert (isinstance (child, Widget))
        child_x = 0
        for (x, _) in self.children:
            if x >= child_x:
                child_x = x + 1
        self.add_child (child, child_x, 0)

    def focus (self, child):
        self.focus_child = child

    def get_size (self):
        grid_width = 0
        grid_height = 0
        for ((x, y), child) in self.children.items ():
            if not child.visible:
                continue
            if x >= grid_width:
                grid_width = x + 1
            if y >= grid_height:
                grid_height = y + 1

        row_heights = [0] * grid_height
        column_widths = [0] * grid_width
        for ((x, y), child) in self.children.items ():
            if not child.visible:
                continue
            (w, h) = child.get_size ()
            if w > column_widths[x]:
                column_widths[x] = w
            if h > row_heights[y]:
                row_heights[y] = h

        width = 0
        for x in range (grid_width):
            width += column_widths[x]
        height = 0
        for y in range (grid_height):
            height += row_heights[y]

        return (width, height)

    def handle_event (self, event):
        if self.focus_child is None:
            return
        self.focus_child.handle_event (event)

    def render (self, frame, theme):
        # Work out size of grid
        width = 0
        height = 0
        for ((x, y), child) in self.children.items ():
            if not child.visible:
                continue
            if x >= width:
                width = x + 1
            if y >= height:
                height = y + 1

        # Get size and scale for each child
        row_heights = [0] * height
        column_widths = [0] * width
        row_scales = [0.0] * height
        column_scales = [0.0] * width
        for ((x, y), child) in self.children.items ():
            if not child.visible:
                continue
            (w, h) = child.get_size ()
            if w > column_widths[x]:
                column_widths[x] = w
            if child.x_scale > column_scales[x]:
                column_scales[x] = child.x_scale
            if h > row_heights[y]:
                row_heights[y] = h
            if child.y_scale > row_scales[y]:
                row_scales[y] = child.y_scale

        # Allocate rows
        for y in range (height):
            available = frame.width
            total_scales = 0.0
            for x in range (width):
                total_scales += column_scales[x]
                available -= column_widths[x]

            if total_scales <= 0.0:
                break

            requested = []
            for x in range (width):
                requested += [available * column_scales[x] / total_scales]

            # Allocate space fairly
            while available > 0:
                current_requested = 0.0
                next_x = 0
                for x in range (width):
                    if requested[x] > current_requested:
                        next_x = x
                        current_requested = requested[x]
                if current_requested <= 0.0:
                    break
                requested[next_x] = max (requested[next_x] - 1.0, 0.0)
                column_widths[next_x] += 1
                available -= 1

        # Allocate columns
        for x in range (width):
            available = frame.height
            total_scales = 0.0
            for y in range (height):
                total_scales += row_scales[y]
                available -= row_heights[y]

            if total_scales <= 0.0:
                break

            requested = []
            for y in range (height):
                requested += [available * row_scales[y] / total_scales]

            # Allocate space fairly
            while available > 0:
                current_requested = 0.0
                next_y = 0
                for y in range (height):
                    if requested[y] > current_requested:
                        next_y = y
                        current_requested = requested[y]
                if current_requested <= 0.0:
                    break
                requested[next_y] = max (requested[next_y] - 1.0, 0.0)
                row_heights[next_y] += 1
                available -= 1

        # Draw chldren
        for ((x, y), child) in self.children.items ():
            if not child.visible:
                continue
            x_offset = 0
            for i in range (x):
                x_offset += column_widths[i]
            w = column_widths[x]
            y_offset = 0
            for i in range (y):
                y_offset += row_heights[i]
            h = row_heights[y]
            child_frame = self.render_child (child, w, h, theme)
            frame.composite (x_offset, y_offset, child_frame)
            if child is self.focus_child and child_frame.cursor is not None:
                frame.cursor = (x_offset + child_frame.cursor[0], y_offset + child_frame.cursor[1])
