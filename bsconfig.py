import os
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

class BoyngHelper(object):
    
    def __init__(self, config, module_name):
        self._config = config
        self._mod_name = module_name
    
    def input(self, name):
        cfg_name = "%s_%s" % (self._mod_name, 
            str(name).strip(' ').upper())
        
        if not self._config.has_key(cfg_name):
            print "value for %s (%s) is: " % (name, cfg_name)
            value = shell_escape(raw_input())
            self._config[cfg_name] = value
        return self._config[cfg_name]


def eval_config(directory, options, err=sys.stderr):
    
    pickle_path = os.path.join(directory, CFG_USERFILE)
    module_name = None
    file_path = ""
    config = {}
    
    for i in os.listdir(directory):
        cfg_match = CFG_FILE.match(i)
        if not (cfg_match is None):
            if module_name is None:
                module_name = cfg_match.group(1)
                file_path = os.path.join(directory, i)
            else:
                sys.stderr.write("only 1 configure-skript per" + 
                    " directory is allowed\n")
                sys.stderr.flush()
                sys.exit(1)
    
    if not (module_name is None):
        module_name = module_name.strip(' ').upper()
        
        if os.path.exists(pickle_path) and (not options.reconfigure):
            f = open(pickle_path, 'r')
            try:
                pick = cPickle.Unpickler(f)
                config = pick.load()
            finally:
                f.close()
        
        env = {'__builtins__' : __builtins__,
            'BOYNG_VERSION' : VERSION,
            'cfg' : BoyngHelper(config, module_name)}
        
        execfile(file_path, env, env)
        
        #config['module'] = module_name
        
        f = open(pickle_path, 'w')
        try:
            pick = cPickle.Pickler(f, 0)
            pick.dump(config)
        finally:
            f.close()
    else:
        if options.verbose:
            err.write("no configure skript found (%s)\n" % directory)
            err.flush()


def do_config(basedir, options):
    
    eval_config(basedir, options)
    
    for i in os.listdir(basedir):
        curr_dir = os.path.join(basedir, i)
        if os.path.isdir(curr_dir):
            do_config(curr_dir, options)

class ModuleNode(object):
    
    def __init__(self, name, path):
        self._name = name
        self._path = path
        self._full = os.path.join(path, CFG_SCRIPTFILE % name)


class Configer(object):
    
    def __init__(self, dirs, options):
        
        self._dirs = dirs
        self._log = logging.getLogger(LOGGER_NAME)
        self._mods = {}
        
        if options.verbose:
            self._log.setLevel(logging.DEBUG)
        
        if len(dirs) <= 0:
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
                
                if (not (sf_match is None) and (not is_a_dir):
                    if found:
                        self._log.critical("only one configure-script" + 
                            " per directory is allowed (%s)" % directory)
                        raise OnlyOneModuleInDirectoryError()
                    else:
                        self._add_module(sf_match.group(1), directory)
                        found = True
                elif is_a_dir:
                    self._load_modules_in_directory(self, fullpath)
    
    def _find_modules(self):
        
        for i in dirs:
            self._load_modules_in_directory(os.path.realpath(i))


def main(args):
    
    parser = optparse.OptionParser(
        usage="usage: %prog cfg [options] basedir [other-directories]")
    
    parser.add_option("-r", "--reconfigure", action="store_true",
        help="deletes old userconfig and reconfigures source code")
    
    parser.add_option("-v", "--verbose", action="store_true",
        help="turns on warnings (to stderr)...")
    
    parser.set_defaults(verbose=False, reconfigure=False)
    
    options, args = parser.parse_args(args)
    
    cfg_obj = Configer(args, options)
