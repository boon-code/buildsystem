import sys
import os
import re
import logging

import bssettings

LOGGER_NAME = 'config'

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


class ConfigException(Exception):
    pass


class NoDirectoryToConfigError(ConfigException):
    pass


class ModuleNameAlreadyUsedError(ConfigException):
    pass

class OnlyOneModuleInDirectoryError(ConfigException):
    pass


class UserConfig(object):
    
    def __init__(self, curr_mod, mods_to_load, configer):
        
        self._mods = mods_to_load
        self._mod = curr_mod
        self._cfg = configer
    
    def 
        

class ModuleNode(object):
    
    def __init__(self, name, path):
        self._name = name
        self._path = path
        self._full = os.path.join(path, 
                bssettings.CFG_SCRIPTFILE % name)
    
    def get_name(self):
        return self._name
    
    def get_path(self):
        return self._path
    
    def get_script_path(self):
        return self._full


class Configer(object):
    
    def __init__(self, dirs, verbose=False):
        
        self._dirs = dirs
        self._log = logging.getLogger(LOGGER_NAME)
        self._mods = {}
        self._mods_exec_list = []
        
        if verbose:
            self._log.setLevel(logging.DEBUG)
        
        if len(self._dirs) <= 0:
            self._log.warning("no directories given!")
            raise NoDirectoryToConfigError()
        else:
            self._find_modules()
    
    def _add_module(self, name, path):
        
        path = os.path.realpath(path)
        
        if name in self._mods:
            if self._mods[name].get_path() != path:
                self._log.critical("i have already found a module" + 
                    " with name '%s'" % name)
                raise ModuleNameAlreadyUsedError()
            else:
                self._log.info("already listed this module: %s" % name)
        else:
            self._mods[name] = ModuleNode(name, path)
            self._log.debug("added module %s (%s)" % (name, path))
    
    def _load_modules_in_directory(self, directory):
        
        found = False
        
        if os.path.isdir(directory):
            for i in os.listdir(directory):
                fullpath = os.path.join(directory, i)
                is_a_dir = os.path.isdir(fullpath)
                sf_match = bssettings.CFG_SCRIPTFILE_RE.match(i)
                
                if (not (sf_match is None)) and (not is_a_dir):
                    if found:
                        self._log.critical("only one configure-script" + 
                            " per directory is allowed (%s)" % directory)
                        raise OnlyOneModuleInDirectoryError()
                    else:
                        self._add_module(sf_match.group(1), directory)
                        found = True
                elif is_a_dir:
                    self._load_modules_in_directory(fullpath)
    
    def _find_modules(self):
        
        for i in self._dirs:
            self._load_modules_in_directory(os.path.realpath(i))
    
    
    def _real_exec_module(self, module):
        
    
    def exec_module(self, name):
        
    
    
    def _exec_modules(self):
        
        self._mods_exec_list = self._mods.values()
        
        while True:
            try:
                curr_mod = self._mods_exec_list.pop()
            except IndexError:
                return
            
            
            self._log.debug("exec module %s" % curr_mod.get_name())
            script_path = curr_mod.get_script_path()
            
            
            
            
            
    
    def show_modules(self):
        
        for (k,v) in self._mods.iteritems():
            print k,v.get_path()


def main(args):
    
    parser = optparse.OptionParser(
        usage="usage: %prog cfg [options] basedir [other-directories]")
    
    parser.add_option("-r", "--reconfigure", action="store_true",
        help="deletes old userconfig and reconfigures source code")
    
    parser.add_option("-v", "--verbose", action="store_true",
        help="turns on warnings (to stderr)...")
    
    parser.set_defaults(verbose=False, reconfigure=False)
    
    options, args = parser.parse_args(args)
    
    cfg_obj = Configer(args, verbose=options.verbose)
