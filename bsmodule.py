import sys
import os
import copy
import logging
import bsfile
import bssettings

LOGGER_NAME = 'module'

import __main__
if 'DEBUG_' in dir(__main__):
    __main__.LOG_LEVEL_ = logging.DEBUG
else:
    DEBUG_ = False

if 'LOG_LEVEL_' in dir(__main__):
    log = logging.getLogger(LOGGER_NAME)
    log.setLevel(__main__.LOG_LEVEL_)
    if len(log.handlers) <= 0:
        st_log = logging.StreamHandler(sys.stderr)
        st_log.setFormatter(
            logging.Formatter("%(name)s : %(threadName)s : %(levelname)s : %(message)s"))
        log.addHandler(st_log)
        del st_log
    del log
else:
    log = logging.getLogger(LOGGER_NAME)
    log.setLevel(logging.CRITICAL)


class ModuleException(Exception):
    pass


class InOutNotAllowedError(ModuleException):
    pass


class CyclingOutputError(ModuleException):
    pass


class DepencyError(ModuleException):
    pass


class SoftDepencyError(DepencyError):
    pass


class ConflictingOrdersError(DepencyError):
    pass


class ModuleNode(object):
    
    def __init__(self, name, path):
        self._log = logging.getLogger(LOGGER_NAME)
        self._uname = name.upper()
        self._path = path
        self._full = os.path.join(path, 
                bssettings.CFG_SCRIPTFILE % name)
        self._in = []
        self._out = []
        self._master = []
        self._usr_config = {}
        self._orders = {}
        self._execuded = False
    
    def get_name(self):
        return self._uname
    
    def get_path(self):
        return self._path
    
    def get_script_path(self):
        return self._full
    
    def is_execuded(self):
        return self._execuded
    
    def add_input(self, module):
        
        if module in self._out:
            self._log.critical("module %s is already input for module %s"
                % (module.get_name(), self._uname))
            raise InOutNotAllowedError()
        elif module in self._in:
            self._log.debug("%s: already added module %s as input"
                % (self._uname, module.get_name()))
        else:
            self._in.append(module)
    
    def add_output(self, module):
        
        if module in self._in:
            self._log.critical("module %s is already output for module %s"
                % (module.get_name(), self._name))
            raise InOutNotAllowedError()
        elif module in self._out:
            self._log.debug("%s: already added module %s as output"
                % (self._uname, module.get_name()))
        else:
            self._out.append(module)
    
    def add_cmaster(self, module):
        
        if module in self._out:
            self._log.critical("%s can't configure it's master %s"
                % (self._uname, module.get_name()))
            raise CyclingOutputError()
        elif module in self._master:
            self._log.debug("%s: already added module %s as master"
                % (self._uname, module.get_name()))
        else:
            self._master.append(module)
    
    def check_depencies(self, usr_class, mods_to_exec, reconfig):
        
        for i in self._in:
            if i in mods_to_exec:
                mods_to_exec.remove(i)
                i.eval_config(usr_class, mods_to_exec, reconfig)
        
        for i in self._master:
            if i in mods_to_exec:
                mods_to_exec.remove(i)
                i.eval_config(usr_class, mods_to_exec, reconfig)
        
        self._log.debug("now checking depencies for module %s"
            % self._uname)
        
        for i in self._in:
            if not i.is_execuded():
                self._log.critical("dep. error in module %s (input %s)"
                    % (self._uname, i.get_name()))
                raise DepencyError()
        
        for i in self._master:
            if not i.is_execuded():
                self._log.warning("%s: master %s not execuded"
                    % (self._uname, i.get_name()))
                raise SoftDepencyError()
        
        self._log.debug("depency checked for module %s" % self._uname)
    
    def get_usr_cfg(self):
        return copy.deepcopy(self._usr_config)
    
    def get_cfg(self, name):
        
        cfg_name = "%s_%s" % (self._uname, name)
        
        if cfg_name in self._usr_config:
            return self._usr_config[cfg_name]
        else:
            return None
    
    def add_cfg(self, name, value, overwrite=False):
        
        cfg_name = "%s_%s" % (self._uname, name)
        
        if (not (cfg_name in self._usr_config)) or overwrite:
            self._usr_config[cfg_name] = value
            return True
        else:
            return False
    
    def submit_order(self, modname, name, value):
        
        modname = modname.upper()
        for i in self._out:
            if modname == i.get_name():
                i._add_order(self, name, value, True)
                return True
        
        return False
    
    def _exec_orders(self):
        
        for (name, order) in self._orders.iteritems():
            self.add_cfg(name, order[0], overwrite=True)
    
    def _add_order(self, module, name, value, overwrite):
        
        if self._orders.has_key(name):
            order = self._orders[name]
            if order[1] == module:
                if overwrite:
                    self._orders[name] = [value, module]
                    return True
                else:
                    return False
            else:
                self._log.critical("can't overwrite %s" % name)
                raise ConflictingOrdersError()
        else:
            self._orders[name] = [value, module]
    
    def _load_config(self):
        
        usr_file = os.path.join(self._path, bssettings.CFG_USERFILE)
        cache_file = os.path.join(self._path, bssettings.CFG_CACHEFILE)
        ccfg = {}
        
        if os.path.exists(usr_file):
            self._usr_config = bsfile.load_cfg(usr_file)
        
        for i in self._in:
            cfg = i.get_usr_cfg()
            ccfg.update(cfg)
        
        return ccfg
    
    def _save_config(self, cache):
        
        usr_file = os.path.join(self._path, bssettings.CFG_USERFILE)
        cache_file = os.path.join(self._path, bssettings.CFG_CACHEFILE)
        
        bsfile.save_cfg(usr_file, self._usr_config)
        bsfile.save_cfg(cache_file, cache)
    
    def eval_config(self, usr_class, mods_to_exec, reconfig):
        
        reconfigure = (self._uname in reconfig)
        self.check_depencies(usr_class, mods_to_exec, reconfig)
        ccfg = self._load_config()
        self._exec_orders()
        usercfg = usr_class(self, ccfg)
        
        env = {'__builtins__' : __builtins__,
            'BS_VERSION' : bssettings.VERSION,
            'cfg' : usercfg}
        
        execfile(self._full, env, env)
        
        env._exec(reconfigure)
        
        self._save_config(ccfg)
        self._execuded = True
    
    def infolist(self):
        
        return {'name' : copy.copy(self._uname),
                'scriptfile' : copy.copy(self._full),
                'in' : [i.get_name() for i in self._in],
                'out' : [i.get_name() for i in self._out]}

