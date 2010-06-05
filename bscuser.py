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
    
    def __init__(self, module, cache, reconfigure=False):
        self._mod = module
        self._ccfg = cache
        self._reconfig = reconfigure

    def input(self, name):
        
        old = self._mod.get_cfg(name)
        
        if old is None:
            print "value for %s is: " % name
            value = shell_escape(raw_input())
            self._mod.add_cfg(name, value)
        elif self._reconfig:
            try:
                print ("value for %s was %s... enter new value or Ctrl+D to exit" %
                    (name, str(old)))
                value = shell_escape(raw_input())
                self._mod.add_cfg(name, value, True)
            except EOFError:
                print "keep old value!"
    
    def _print_list(self, name, darray):
        
        try:
            for (i,v) in enumerate(darray):
                print "%d %s" % (i, v)
            print "choose var '%s' from list:" % name
            number = raw_input()
            self._mod.add_cfg(name, darray[int(number)])
        except (IndexError, ValueError):
            return self._print_list(name, darray)
    
    def choose(self, name, darray):
        
        old = self._mod.get_cfg(name)
        
        if old is None:
            self._print_list(name, darray)
        elif self._reconfig:
            try:
                self._print_list(name, darray)
            except EOFError:
                print "keep old value"
    
    def sub_write(self, modname, name, value):
        
        # overwrite True enables a module to overwrite it's settings
        self._mod.submit_order(modname, name, value, True)
    
    def read(self, name):
        
        value = self._mod.get_cfg(name)
        if value is None:
            raise MissingEntryError()
        else:
            return value
    
    def write(self, name, value):
        
        self._mod.add_cfg(name, value, True)
    
    def inread(self, name):
        
        if self._ccfg.has_key(name):
            return self._ccfg[name]
        else:
            raise MissingEntryError()
