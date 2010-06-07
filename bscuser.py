import sys
import os
import copy
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


class CyclingDepencyError(UserConfigException):
    pass


class WasNotAskedError(UserConfigException):
    pass


class BasicInput(object):
    
    def __init__(self, name, value, messages):
        
        self._dict = {'name' : name, 'old' : value, 'value' : None}
        self._quest = messages['question'] % self._dict
        self._old = messages['old'] % self._dict
        self._asked = False
        if 'help' in messages:
            self._help = messages['help'] % self._dict
        else:
            self._help = None
    
    def _real_ask(self, reconfigure):
        raise UnimplementedException()
    
    def _check_depency(self, in_obj):
        pass
    
    def _ask(self, reconfigure):
        
        if self._asked:
            value = self._dict['value']
        else:
            value = self._dict['old']
            
            if (value is None) or reconfigure:
                value = self._real_ask(reconfigure)
            else:
                value = self._dict['old']
            
            self._dict['value'] = value
            self._asked = True
        return value
    
    def _eval(self, module, reconfigure):
        
        value = self._ask(reconfigure)
        module.add_cfg(self._dict['name'], value, True)
    
    def read(self):
        
        if self._asked:
            return self._dict['value']
        else:
            raise WasNotAskedError()


class UserExprInput(BasicInput):
    
    def __init__(self, name, value, messages):
        
        if not ('question' in messages):
            messages['question'] = "Enter Expression for %(name)s"
        if not ('old' in messages):
            messages['old'] = "To Keep old value '%(old)s' press Ctrl+D"
        
        BasicInput.__init__(self, name, value, messages)
    
    def _real_ask(self, reconfigure):
        
        print self._quest
        if reconfigure:
            print self._old
        if self._help:
            print self._help
        try:
            value = shell_escape(raw_input())
            print "configuring: %s = %s" % (self._dict['name'], value)
            return value
        except EOFError:
            if reconfigure:
                print "keep old value: %(name)s = %(old)s" % self._dict
                return self._dict['old']
            else:
                raise SkipException()


class UserStringInput(BasicInput):
    
    def __init__(self, name, value, messages):
        
        if not ('question' in messages):
            messages['question'] = "Enter String for %(name)s"
        if not ('old' in messages):
            messages['old'] = "To Keep old value '%(old)s' press Ctrl+D"
        
        BasicInput.__init__(self, name, value, messages)
    
    def _real_ask(self, reconfigure):
        
        print self._quest
        if reconfigure:
            print self._old
        if self._help:
            print self._help
        try:
            value = shell_escape('"%s"' % raw_input())
            print "configuring: %s = %s" % (self._dict['name'], value)
            return value
        except EOFError:
            if reconfigure:
                print "keep old value: %(name)s = %(old)s" % self._dict
                return self._dict['old']
            else:
                raise SkipException()


class UserListInput(BasicInput):
    
    def __init__(self, name, value, darray, messages):
        
        if not ('question' in messages):
            messages['question'] = "Choose var %(name)s from list:"
        if not ('old' in messages):
            messages['old'] = "To Keep old value '%(old)s' press Ctrl+D"
        
        BasicInput.__init__(self, name, value, messages)
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
            return self._darray[int(number)]
        except (IndexError, ValueError):
            print "invalid choice"
            return self._real_ask(reconfigure)
        except EOFError:
            if reconfigure:
                print "keep old value: %(name)s = %(old)s" % self._dict
                return self._dict['old']
            else:
                raise SkipException()


class SimpleCallTarget(BasicInput):
    
    def __init__(self, name, value, deps, function):
        
        BasicInput.__init__(self, name, value, {})
        self._func = function
        for i in deps:
            i._check_depency(self)
        self._deps = frozenset(deps)
    
    def _real_ask(self, reconfigure):
        
        return self._func(self, *self._deps)
    
    def _check_depency(self, in_obj):
        
        if in_obj in self._deps:
            raise CyclingDepencyError()
    
    def _add_depency(self, deps):
        
        for i in deps:
            i._check_depency(self)
        self._deps = self._deps.union(deps)
    
    def _exec_deps(self, reconfigure):
        
        for i in self._deps:
            i._ask(reconfigure)
    
    def _ask(self, reconfigure=False):
        
        self._exec_deps(reconfigure)
        return BasicInput._ask(self, True)


class SimpleTextConfig(object):
    
    def __init__(self, module, cache):
        self._mod = module
        self._ccfg = cache
        self._objs = []

    def expr(self, name, **messages):
        
        value = self._mod.get_cfg(name)
        obj = UserExprInput(name, value, messages)
        self._objs.append(obj)
        return obj
    
    def string(self, name, **messages):
        
        value = self._mod.get_cfg(name)
        obj = UserStringInput(name, value, messages)
        self._objs.append(obj)
        return obj
    
    def choose(self, name, darray, **messages):
        
        value = self._mod.get_cfg(name)
        obj = UserListInput(name, value, darray, messages)
        self._objs.append(obj)
        return obj
    
    def bind(self, name, function, *depencies):
        "bind function + depencies to target 'name'"
        
        value = self._mod.get_cfg(name)
        obj = SimpleCallTarget(name, value, depencies, function)
        self._objs.append(obj)
        return obj
    
    def sub_write(self, modname, name, value):
        
        self._mod.submit_order(modname, name, value)
    
    def inread(self, name):
        
        if self._ccfg.has_key(name):
            return self._ccfg[name]
        else:
            raise MissingEntryError()
    
    def _eval(self, reconfigure=False):
        
        obj_reverse = copy.copy(self._objs)
        obj_reverse.reverse()
        for i in obj_reverse:
            i._eval(self._mod, reconfigure)
