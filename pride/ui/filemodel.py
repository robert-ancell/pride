# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

import os
import unicodedata

from .treemodel import TreeModel

class FileModel (TreeModel):
    def __init__ (self, path = '.'):
        TreeModel.__init__ (self)
        self.files = os.listdir (path)
        self.files.sort ()

    def get_size (self):
        return len (self.files)

    def _get_icon (self, path):
        path = path.lower ()
        if path.endswith ('.py'):
            return unicodedata.lookup ('SNAKE')
        elif path.endswith ('.txt') or path.endswith ('.md') or path.endswith ('.xml') or path in ('README'):
            return unicodedata.lookup ('PAGE FACING UP')
        elif path.endswith ('.png') or path.endswith ('.jpg') or path.endswith ('.jpeg') or path.endswith ('.svg'):
            return unicodedata.lookup ('FRAME WITH PICTURE') + '\ufe0f'
        else:
            return '  '

    def get_label (self, index):
        path = self.files[index]
        return (self._get_icon (path) + ' ' + path, None, None)

    def get_item (self, index):
        return self.files[index]
