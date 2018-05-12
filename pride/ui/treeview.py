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
    def __init__ (self, model = None, callback = None):
        Widget.__init__ (self)
        if model is None:
            self.model = TreeModel ()
        else:
            self.model = model
        self.callback = callback
        self.set_scale (1.0, 1.0)
        self.selected = 0
        self.start = 0

    def get_size (self):
        return (0, 1)

    def handle_key_event (self, event):
        if event.key == Key.UP:
            self.selected = max (self.selected - 1, 0)
        elif event.key == Key.DOWN:
            self.selected = min (self.selected + 1, self.model.get_size () - 1)
        elif event.key == Key.ENTER:
            if self.callback is not None:
                self.callback (self.model.get_item (self.selected))

    def render (self, frame):
        # Scroll display to show cursor
        while self.selected - self.start < 0:
            self.start -= 1
        while self.selected - self.start >= frame.height:
            self.start += 1

        frame.clear ()
        y = 0
        for i in range (self.start, self.model.get_size ()):
            if i == self.selected:
                background = '#0000FF'
                frame.cursor = (0, y)
            else:
                background = '#000000'
            label = self.model.get_label (i).ljust (frame.width)
            frame.render_text (0, y, label, background = background)
            y += 1
