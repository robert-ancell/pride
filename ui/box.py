# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .frame import Frame
from .widget import Widget

class Box (Widget):
    def __init__ (self):
        Widget.__init__ (self)
        self.child = None

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
        # FIXME: Different styles
        frame.render_text (0, 0, '╭')
        frame.render_text (frame.width - 1, 0, '╮')
        frame.render_text (0, frame.height - 1, '╰')
        frame.render_text (frame.width - 1, frame.height - 1, '╯')
        for x in range (1, frame.width - 1):
            frame.render_text (x, 0, '─')
            frame.render_text (x, frame.height - 1, '─')
        for y in range (1, frame.height - 1):
            frame.render_text (0, y, '│')
            frame.render_text (frame.width - 1, y, '│')
