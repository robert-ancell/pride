# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .frame import Frame
from .container import Container

class BoxStyle:
    SQUARE = 'square'
    CURVED = 'curved'
    BOLD   = 'bold'
    DOUBLE = 'double'
    WIDE   = 'wide'

class Box (Container):
    def __init__ (self, style = BoxStyle.CURVED, foreground = None, background = None):
        Container.__init__ (self)
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
            (width, height) = self.child.get_size ()
        else:
            (width, height) = (0, 0)
        return (width + 2, height + 2)

    def render (self, frame, theme):
        if self.foreground is None:
            foreground = theme.box_border
        else:
            foreground = self.foreground
        if self.background is None:
            background = theme.box_background
        else:
            background = self.background
        frame.clear (background)
        if self.child is not None and self.child.visible:
            child_frame = self.render_child (self.child, frame.width - 2, frame.height - 2, theme)
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
        frame.render_text (0, 0, top_left, foreground, background)
        frame.render_text (frame.width - 1, 0, top_right, foreground, background)
        frame.render_text (0, frame.height - 1, bottom_left, foreground, background)
        frame.render_text (frame.width - 1, frame.height - 1, bottom_right, foreground, background)
        for x in range (1, frame.width - 1):
            frame.render_text (x, 0, top_horizontal, foreground, background)
            frame.render_text (x, frame.height - 1, bottom_horizontal, foreground, background)
        for y in range (1, frame.height - 1):
            frame.render_text (0, y, left_vertical, foreground, background)
            frame.render_text (frame.width - 1, y, right_vertical, foreground, background)
