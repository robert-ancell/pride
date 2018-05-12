# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .treemodel import TreeModel

class ListModel (TreeModel):
    def __init__ (self):
        TreeModel.__init__ (self)
        self.items = []

    def add_item (self, label, item = None):
        if item is None:
            item = label
        self.items.append ((label, item))

    def get_size (self):
        return len (self.items)

    def get_label (self, index):
        return self.items[index][0]

    def get_item (self, index):
        return self.items[index][1]
