# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .keyinputevent import Key
from .treemodel import TreeModel
from .widget import Widget

class TreeView (Widget):
    def __init__ (self, model = None):
        Widget.__init__ (self)
        if model is None:
            self.model = TreeModel ()
        else:
            self.model = model
        self.set_scale (1.0, 1.0)
        self.selected = 0

    def get_size (self):
        return (0, 1)

    def handle_key_event (self, event):
        if event.key == Key.UP:
            self.selected = max (self.selected - 1, 0)
        elif event.key == Key.DOWN:
            self.selected = min (self.selected + 1, self.model.get_size () - 1)
        elif event.key == Key.ENTER:
            pass #self.activated ()

    def render (self, frame):
        frame.clear ()
        for i in range (self.model.get_size ()):
            if i == self.selected:
                background = '#0000FF'
                frame.cursor = (0, i)
            else:
                background = '#000000'
            label = self.model.get_label (i).ljust (frame.width)
            frame.render_text (0, i, label, background = background)
