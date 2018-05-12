# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .widget import Widget

class Tabs (Widget):
    def __init__ (self):
        Widget.__init__ (self)
        self.tabs = []
        self.selected = 0
        self.set_scale (1.0, 0.0)

    def add_child (self, label):
        self.tabs.append (label)

    def set_selected (self, index):
        self.selected = index

    def get_size (self):
        return (0, 1)

    def render (self, frame):
        frame.clear ("#0000FF")
        row = 0
        for (i, label) in enumerate (self.tabs):
            if i == self.selected:
                background = '#FF0000'
            else:
                background = '#0000FF'
            frame.render_text (row, 0, label, background = background)
            row += len (label)
            frame.render_text (row, 0, '|', background = '#0000FF')
            row += 1
