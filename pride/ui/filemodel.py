# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

import os

from .treemodel import TreeModel

class FileModel (TreeModel):
    def __init__ (self, path = '.'):
        TreeModel.__init__ (self)
        self.files = os.listdir (path)
        self.files.sort ()

    def get_size (self):
        return len (self.files)

    def get_label (self, index):
        return self.files[index]

    def get_item (self, index):
        return self.files[index]
