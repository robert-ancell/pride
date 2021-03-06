# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .frame import Frame
from .widget import Widget

class Container (Widget):
    def __init__ (self):
        Widget.__init__ (self)
        self._frames = {}
        self.focus_child = None

    def focus (self, child):
        if self.focus_child is child:
            return
        if self.focus_child is not None:
            self.focus_child.set_focus (False)
        self.focus_child = child
        if child is not None:
            child.set_focus (True)

    def render_child (self, child, width, height, theme):
        frame = self._frames.get (child)
        if frame is None or (frame.width, frame.height) != (width, height):
            frame = Frame (width, height)
            self._frames[child] = frame
        child.render_aligned (frame, theme)
        return frame

    def handle_event (self, event):
        if self.focus_child is not None and self.focus_child.handle_event (event):
            return True
        else:
            return False
