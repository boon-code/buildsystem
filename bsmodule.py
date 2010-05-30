import os
import copy
import logging
import cPickle
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
    
    def get_name(self):
        return self._uname
    
    def get_path(self):
        return self._path
    
    def get_script_path(self):
        return self._full
    
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
    
    def eval_config(self, user_class, mods_to_exec, reconfig):
        
        usr_path = os.path.join(self._path, bssettings.CFG_USERFILE)
        cache_path = os.path.join(self._path, bssettings.CFG_CACHEFILE)
        
        if os.path.exists(usr_path) and (not (self._uname in reconfig)):
            f = open(usr_path, 'r')
            try:
                pick = cPickle.Unpickler(f)
                config = pick.load()
            finally:
                f.close()
        
        for reqi in self._in:
            if reqi in mods_to_exec:
                mods_to_exec.remove(reqi)
                reqi.eval_config(mods_to_exec, reconfig)
        
        for cmi in self._master:
            if cmi in mods_to_exec:
                mods_to_exec.remove(cmi)
                cmi.eval_config(mods_to_exec, reconfig)
        
        usercfg = user_class()
        
        env = {'__builtins__' : __builtins__,
            'BS_VERSION' : bssettings.VERSION,
            'cfg' : usercfg}
        
        execfile(self._full, env, {})
        
        f = open(usr_path, 'w')
        try:
            pick = cPickle.Pickler(f, 0)
            pick.dump(usercfg.clone_usr_cfg())
        finally:
            f.close()
    
    def infolist(self):
        
        return {'name' : copy.copy(self._uname),
                'scriptfile' : copy.copy(self._full),
                'in' : [i.get_name() for i in self._in],
                'out' : [i.get_name() for i in self._out]}

