# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .frame import Frame
from .widget import Widget

class Stack (Widget):
    def __init__ (self):
        Widget.__init__ (self)
        self.children = []
        self.set_scale (1.0, 1.0)

    def add_child (self, child):
        self.children.insert (0, child)

    def raise_child (self, child):
        self.children.remove (child)
        self.children.insert (0, child)

    def get_size (self):
        width = 0
        height = 0
        for child in self.children:
            (w, h) = child.get_size ()
            width = max (width, w)
            height = max (height, h)
        return (width, height)

    def handle_event (self, event):
        open ('debug.log', 'a').write ('stack key {}\n'.format (event))
        for child in self.children:
            if child.visible:
                child.handle_event (event)
                return

    def render (self, frame):
        # FIXME: Work out if widgets would be covered and skip rendering
        # FIXME: Take colour out of covered children
        have_cursor = False
        for child in reversed (self.children):
            if not child.visible:
                continue
            child.render_aligned (frame)
