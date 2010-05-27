#! /usr/bin/env python
# -*- coding: utf-8 -*-
# my build system

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
