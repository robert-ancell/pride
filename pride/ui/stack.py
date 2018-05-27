# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .frame import Frame
from .container import Container

class Stack (Container):
    def __init__ (self):
        Container.__init__ (self)
        self.children = []
        self.set_scale (1.0, 1.0)

    def _update_focus (self):
        focus_child = None
        for child in self.children:
            if child.visible:
                focus_child = child
                break
        self.focus (focus_child)

    def add_child (self, child):
        self.children.append (child)
        self._update_focus ()

    def raise_child (self, child):
        if self.children[0] is child:
            return
        self.children.remove (child)
        self.children.insert (0, child)
        self._update_focus ()

    def get_size (self):
        width = 0
        height = 0
        for child in self.children:
            (w, h) = child.get_size ()
            width = max (width, w)
            height = max (height, h)
        return (width, height)

    def render (self, frame, theme):
        self._update_focus ()
        # FIXME: Work out if widgets would be covered and skip rendering
        # FIXME: Take colour out of covered children
        have_cursor = False
        for child in reversed (self.children):
            if not child.visible:
                continue
            child.render_aligned (frame, theme)
