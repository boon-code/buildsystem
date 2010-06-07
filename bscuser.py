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


class UnimplementedException(UserConfigException):
    pass


class BasicInput(object):
    
    def __init__(self, name, value, question, old_text, help=None):
        
        self._dict = {'name' : name, 'old' : value, 'value' : None}
        self._quest = question % self._dict
        self._old = old_text % self._dict
        if not (help is None):
            self._help = help % self._dict
        else:
            self._help = None
    
    def _real_ask(self, reconfigure):
        raise UnimplementedException()
    
    def _ask(self, reconfigure=False):
        
        if self._dict['old'] is None:
            return self._real_ask(reconfigure)
        elif reconfigure:
            return self._real_ask(True)
        else:
            return value


class UserExprInput(BasicInput):
    
    def __init__(self, name, value, help=None,
            question="Enter Expression for %(name)s",
            old_text="To Keep old value '%(old)s' press Ctrl+D"):
        
        BasicInput.__init__(self, name, value, question, old_text,
            help=help)
    
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
        return self._dict['value']


class UserTextInput(BasicInput):
    
    def __init__(self, name, value, help=None,
            question="Enter String for %(name)s",
            old_text="To Keep old value '%(old)s' press Ctrl+D"):
        
        BasicInput.__init__(self, name, value, question, old_text,
            help=help)
    
    def _real_ask(self, reconfigure):
        
        print self._quest
        if reconfigure:
            print self._old
        if self._help:
            print self._help
        try:
            self._dict['value'] = ('"%s"' % shell_escape(raw_input()))
            print "configuring: %(name)s = %(value)s" % self._dict
        except EOFError:
            if reconfigure:
                self._dict['value'] = self._dict['old']
                print "keep old value: %(name)s = %(value)s" % self._dict
            else:
                raise SkipException()
        return self._dict['value']


class UserListInput(BasicInput):
    
    def __init__(self, name, value, darray, help=None,
            question="Choose var %(name)s from list:",
            old_text="To Keep old value '%(old)s' press Ctrl+D"):
        
        BasicInput.__init__(self, name, value, question, old_text,
            help=help)
        self._darray = darray
    
    def _real_ask(self, reconfigure):
        
        for (i,v) in enumerate(self._darray):
            print "%d %s" % (i, v)
        print self._quest
        if reconfigure:
            print self._old
        if self._help:
            print self._help
        try:
            number = raw_input()
            self._dict['value'] = self._darray[int(number)]
        except (IndexError, ValueError):
            print "invalid choice"
            return self._real_ask(reconfigure)
        except EOFError:
            if reconfigure:
                self._dict['value'] = self._dict['old']
                print "keep old value: %(name)s = %(value)s" % self._dict
            else:
                raise SkipException()
        return self._dict['value']


class UserConfig(object):
    
    def __init__(self, module, cache, reconfigure=False):
        self._mod = module
        self._ccfg = cache
        self._reconfig = reconfigure

    def in_expr(self, name):
        
        obj = UserExprInput(name, self._mod.get_cfg(name)
        return obj
    
    def in_string(self, name):
        
        obj = UserTextInput(name, self._mod.get_cfg(name))
        return obj
    
    def choose(self, name, darray):
    
        obj = UserListInput(name, self._mod.get_cfg(name), darray)
        return obj
    
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
