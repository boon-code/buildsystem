import sys
import os
import cPickle
import bssettings

def shell_escape(value):
    value = value.replace('\\', '\\\\')
    value = value.replace('"', '\\"')
    value = value.replace('$', '\$')
    return value


class UserConfigException(Exception):
    pass


class MissingEntryError(UserConfigException):
    pass


class UserConfig(object):
    
    def __init__(self, module, cache):
        self._mod = module
        self._ccfg = cache
        self._overwrite = True

    def input(self, name):
        
        old = self._mod.get_cfg(name)
        
        if old is None:
            print "value for %s is: " % name
            value = shell_escape(raw_input())
            self._mod.add_cfg(name, value, self._overwrite)
        else:
            try:
                print ("value for %s was %s... enter new value or Ctrl+D to exit" %
                    (name, str(old)))
                value = shell_escape(raw_input())
                self._mod.add_cfg(name, value, True)
            except EOFError:
                print "keep old value!"
    
    def sub_write(self, modname, name, value):
        
        self._mod.submit_order(modname, name, value, self._overwrite)
    
    def read(self, name):
        
        value = self._mod.get_cfg(name)
        if value is None:
            raise MissingEntryError()
        else:
            return value
    
    def inread(self, name):
        
        if self._ccfg.has_key(name):
            return self._ccfg[name]
        else:
            raise MissingEntryError()
