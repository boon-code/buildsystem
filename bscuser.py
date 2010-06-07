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


class SkipException(UserConfigException):
    pass


class UserExprInput(object):
    
    def __init__(self, name, value, help=None,
            question="Enter Expression for %(name)s",
            old_text="To Keep old value '%(old)s' press Ctrl+D"):
        
        self._dict = {'name' : name, 'old' : value, 'value' : None}
        self._quest = question % self._dict
        self._old = old_text % self._dict
        if not (help is None):
            self._help = help % self._dict
        else:
            self._help = None
    
    def _real_ask(self, reconfigure):
        
        print self._quest
        
        if reconfigure:
            print self._old
        
        if self._help:
            print self._help
        
        try:
            self._dict['value'] = shell_escape(raw_input())
            print "configuring: %(name)s = %(value)s" % self._dict
        except EOFError:
            if reconfigure:
                self._dict['value'] = self._dict['old']
                print "keep old value: %(name)s = %(value)s" % self._dict
            else:
                raise SkipException()
    
    def _ask(self, reconfigure=False):
        


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
