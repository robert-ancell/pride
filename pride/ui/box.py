# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .frame import Frame
from .widget import Widget

class BoxStyle:
    SQUARE = 'square'
    CURVED = 'curved'
    BOLD   = 'bold'
    DOUBLE = 'double'
    WIDE   = 'wide'

class Box (Widget):
    def __init__ (self, style = BoxStyle.CURVED, foreground = '#FFFFFF', background = '#000000'):
        Widget.__init__ (self)
        self.child = None
        self.style = style
        self.foreground = foreground
        self.background = background

    def set_child (self, child):
        self.child = child

    def handle_event (self, event):
        if self.child is None:
            return
        if self.child.visible:
            self.child.handle_event (event)

    def get_size (self):
        if self.child is not None and self.child.visible:
            (height, width) = self.child.get_size ()
        else:
            (height, width) = (0, 0)
        return (height + 2, width + 2)

    def render (self, frame):
        if self.child is not None and self.child.visible:
            child_frame = Frame (frame.width - 2, frame.height - 2)
            self.child.render_aligned (child_frame)
            frame.composite (1, 1, child_frame)
        if self.style == BoxStyle.SQUARE:
            top_left = '┌'
            top_right = '┐'
            bottom_left = '└'
            bottom_right = '┘'
            top_horizontal = '─'
            bottom_horizontal = '─'
            left_vertical = '│'
            right_vertical = '│'
        elif self.style == BoxStyle.CURVED:
            top_left = '╭'
            top_right = '╮'
            bottom_left = '╰'
            bottom_right = '╯'
            top_horizontal = '─'
            bottom_horizontal = '─'
            left_vertical = '│'
            right_vertical = '│'
        elif self.style == BoxStyle.BOLD:
            top_left = '┏'
            top_right = '┓'
            bottom_left = '┗'
            bottom_right = '┛'
            top_horizontal = '━'
            bottom_horizontal = '━'
            left_vertical = '┃'
            right_vertical = '┃'
        elif self.style == BoxStyle.DOUBLE:
            top_left = '╔'
            top_right = '╗'
            bottom_left = '╚'
            bottom_right = '╝'
            top_horizontal = '═'
            bottom_horizontal = '═'
            left_vertical = '║'
            right_vertical = '║'
        elif self.style == BoxStyle.WIDE:
            top_left = '▛'
            top_right = '▜'
            bottom_left = '▙'
            bottom_right = '▟'
            top_horizontal = '▀'
            bottom_horizontal = '▄'
            left_vertical = '▌'
            right_vertical = '▐'
        else:
            top_left = '?'
            top_right = '?'
            bottom_left = '?'
            bottom_right = '?'
            top_horizontal = '?'
            bottom_horizontal = '?'
            left_vertical = '?'
            right_vertical = '?'
        frame.render_text (0, 0, top_left, self.foreground, self.background)
        frame.render_text (frame.width - 1, 0, top_right, self.foreground, self.background)
        frame.render_text (0, frame.height - 1, bottom_left, self.foreground, self.background)
        frame.render_text (frame.width - 1, frame.height - 1, bottom_right, self.foreground, self.background)
        for x in range (1, frame.width - 1):
            frame.render_text (x, 0, top_horizontal, self.foreground, self.background)
            frame.render_text (x, frame.height - 1, bottom_horizontal, self.foreground, self.background)
        for y in range (1, frame.height - 1):
            frame.render_text (0, y, left_vertical, self.foreground, self.background)
            frame.render_text (frame.width - 1, y, right_vertical, self.foreground, self.background)
