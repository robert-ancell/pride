# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .inputevent import InputEvent

class Key:
    ENTER     = 'enter'
    TAB       = 'tab'
    UP        = 'up'
    DOWN      = 'down'
    LEFT      = 'left'
    RIGHT     = 'right'
    BACKSPACE = 'backspace'
    HOME      = 'home'
    END       = 'end'
    PAGE_UP   = 'page-up'
    PAGE_DOWN = 'page-down'
    DELETE    = 'delete'
    INSERT    = 'insert'
    F1        = 'F1'
    F2        = 'F2'
    F3        = 'F3'
    F4        = 'F4'
    F5        = 'F5'
    F6        = 'F6'
    F7        = 'F7'
    F8        = 'F8'
    F9        = 'F9'

class KeyInputEvent (InputEvent):
    def __init__ (self, key):
        self.key = key

    def __str__ (self):
        return 'KeyInputEvent({})'.format (self.key)