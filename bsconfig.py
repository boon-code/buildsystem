import sys
import os
import re
import shlex
import copy
import logging
import optparse

import bsmodule
import bscuser
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


class ConfigManager(object):
    
    def __init__(self, dirs, verbose=False):
        
        self._dirs = dirs
        self._log = logging.getLogger(LOGGER_NAME)
        self._mods = {}
        
        if verbose:
            self._log.setLevel(logging.DEBUG)
        
        if len(self._dirs) <= 0:
            self._log.warning("no directories given!")
            raise NoDirectoryToConfigError()
        else:
            self.find_modules()
            self.load_module_extensions()
    
    def _add_module(self, name, path):
        
        path = os.path.realpath(path)
        unique_name = name.upper()
        
        if unique_name in self._mods:
            if self._mods[unique_name].get_path() != path:
                self._log.critical("i have already found a module" + 
                    " with name '%s'" % unique_name)
                raise ModuleNameAlreadyUsedError()
            else:
                self._log.info("already listed this module: %s"
                     % unique_name)
        else:
            self._mods[unique_name] = bsmodule.ModuleNode(name, path)
            self._log.debug("added module %s (%s)" % (unique_name, path))
    
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
    
    def find_modules(self):
        
        for i in self._dirs:
            self._load_modules_in_directory(os.path.realpath(i))
    
    def _parse_extcmd(self, cmd_line, module):
        
        args = shlex.split(cmd_line)
        
        if len(args) > 0:
            if args[0] in ('input', 'in'):
                for i in args[1:]:
                    uname = i.upper()
                    if self._mods.has_key(uname):
                        self._log.debug("add module %s" % i)
                        module.add_input(self._mods[uname])
                    else:
                        self._log.warning("couldn't find module %s" % i)
            elif args[0] in ('output', 'out'):
                for i in args[1:]:
                    uname = i.upper()
                    if self._mods.has_key(uname):
                        self._log.debug("add output module %s" % i)
                        module.add_output(self._mods[uname])
                        self._mods[uname].add_cmaster(module)
                    else:
                        self._log.warning("couldn't find module %s" % i)
    
    def load_module_extensions(self):
        
        for curr_mod in self._mods.values():
            
            self._log.debug("try load module extension (module %s)"
                % curr_mod.get_name())
            script_path = curr_mod.get_script_path()
            f = open(script_path, 'r')
            try:
                for line in f:
                    ext_match = bssettings.CFG_EXTENSION_RE.match(line)
                    if not (ext_match is None):
                        cmd = ext_match.group(1)
                        self._log.debug("extension command: '%s'" % cmd)
                        self._parse_extcmd(cmd, curr_mod)
            finally:
                f.close()
    
    def exec_modules(self):
        
        mods = self._mods.values()
        while True:
            try:
                curr_mod = mods.pop()
            except IndexError:
                return
            
            # still need the reconfigure thing..
            
            curr_mod.eval_config(bscuser.UserConfig, mods, {})
    
    def show_modules(self):
        
        for (k,v) in self._mods.iteritems():
            print k
            l = v.infolist()
            print "  name:", l['name']
            print "  script:", l['scriptfile']
            print "  inputs:", l['in']
            print "  outputs:", l['out']


def main(args):
    
    parser = optparse.OptionParser(
        usage="usage: %prog cfg [options] basedir [other-directories]")
    
    parser.add_option("-r", "--reconfigure", action="store_true",
        help="deletes old userconfig and reconfigures source code")
    
    parser.add_option("-v", "--verbose", action="store_true",
        help="turns on warnings (to stderr)...")
    
    parser.add_option("-s", "--show", action="store_true",
        help="shows modules")
    
    parser.set_defaults(verbose=False, reconfigure=False)
    
    options, args = parser.parse_args(args)
    
    cfg_obj = ConfigManager(args[1:], verbose=options.verbose)
    
    if options.show:
        cfg_obj.show_modules()
    else:
        cfg_obj.exec_modules()
