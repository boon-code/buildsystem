import sys
import os
import copy
import cPickle
import Queue
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


class ValueCheckException(UserConfigException):
    pass


class UnimplementedException(UserConfigException):
    pass


class CyclingDepencyError(UserConfigException):
    pass


class WasNotAskedError(UserConfigException):
    pass


class BasicInput(object):
    
    def __init__(self, name, value, options):
        
        self._dict = {'name' : name, 'old' : value, 'value' : None}
        self._quest = options['question'] % self._dict
        self._old = options['old'] % self._dict
        self._asked = False
        if 'help' in options:
            self._help = options['help'] % self._dict
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
                # let's think about this...
                #if isinstance(value, BasicInput):
                #    value = value._ask()
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
    
    def __init__(self, name, value, options):
        
        if not ('question' in options):
            options['question'] = "Enter Expression for %(name)s"
        if not ('old' in options):
            options['old'] = "To Keep old value '%(old)s' press Ctrl+D"
        
        BasicInput.__init__(self, name, value, options)
        
        self._opts = options
    
    def _real_ask(self, reconfigure):
        
        print self._quest
        if reconfigure:
            print self._old
        if self._help:
            print self._help
        try:
            value = shell_escape(raw_input())
            if "check" in self._opts:
                try:
                    result = self._opts.check(value)
                    if not result:
                        raise ValueCheckException()
                except TypeError:
                    print "something wrong with check funtion..."
                    print "ignoring..."
            print "configuring: %s = %s" % (self._dict['name'], value)
            return value
        except EOFError:
            if reconfigure:
                print "keep old value: %(name)s = %(old)s" % self._dict
                return self._dict['old']
            else:
                raise SkipException()


class UserStringInput(BasicInput):
    
    def __init__(self, name, value, options):
        
        if not ('question' in options):
            options['question'] = "Enter String for %(name)s"
        if not ('old' in options):
            options['old'] = "To Keep old value '%(old)s' press Ctrl+D"
        
        BasicInput.__init__(self, name, value, options)
    
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
    
    def __init__(self, name, value, darray, options):
        
        if not ('question' in options):
            options['question'] = "Choose var %(name)s from list:"
        if not ('old' in options):
            options['old'] = "To Keep old value '%(old)s' press Ctrl+D"
        
        self._remove = False
        if 'remove' in options:
            if options['remove']:
                self._remove = True
        
        BasicInput.__init__(self, name, value, options)
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
        except (IndexError, ValueError, KeyError):
            print "invalid choice"
            return self._real_ask(reconfigure)
        except EOFError:
            if reconfigure:
                print "keep old value: %(name)s = %(old)s" % self._dict
                return self._dict['old']
            else:
                raise SkipException()
    
    def _ask(self, reconfigure):
        
        ret = BasicInput._ask(self, reconfigure)
        
        if self._remove:
            if ret in self._darray:
                self._darray.remove(ret)
        return ret


class SimpleCallTarget(BasicInput):
    
    def __init__(self, name, value, deps, function, options):
        
        messages = {'question' : '', 'old' : ''}
        BasicInput.__init__(self, name, value, messages)
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
    
    def _eval(self, module, reconfigure):
        
        self._exec_deps(reconfigure)
        if self._dict['name'] is None:
            return self._real_ask(reconfigure)
        else:
            BasicInput._eval(self, module, True)


class SimpleTextConfig(object):
    
    def __init__(self, module, cache):
        self._mod = module
        self._ccfg = cache
        self._objs = Queue.Queue()
    
    def _input(self, name, options, class_type):
        
        value = self._mod.get_cfg(name)
        obj = class_type(name, value, options)
        self._objs.put(obj)
        return obj

    def expr(self, name, **options):
        return self._input(name, options, UserExprInput)
    
    def string(self, name, **options):
        return self._input(name, options, UserStringInput)
    
    def choose(self, name, darray, **options):
        
        value = self._mod.get_cfg(name)
        obj = UserListInput(name, value, darray, options)
        self._objs.put(obj)
        return obj
    
    def bind(self, name, function, *depencies, **options):
        "bind function + depencies to target 'name'"
        
        value = self._mod.get_cfg(name)
        obj = SimpleCallTarget(name, value, depencies, function, options)
        self._objs.put(obj)
        return obj
    
    def sub_write(self, modname, name, value):
        
        self._mod.submit_order(modname, name, value)
    
    def inread(self, name):
        
        if self._ccfg.has_key(name):
            return self._ccfg[name]
        else:
            raise MissingEntryError()
    
    def _eval(self, reconfigure=False):
        
        try:
            while True:
                obj = self._objs.get(block=False)
                try:
                    obj._eval(self._mod, reconfigure)
                except SkipException:
                    print 'skip'
                    self._objs.put(obj)
                except ValueCheckException:
                    print 'value error'
                    self._objs.put(obj)
        except Queue.Empty:
            pass
