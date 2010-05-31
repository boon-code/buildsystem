import sys
import os
import types
import optparse
import cPickle
import bssettings

class CollectException(Exception):
    pass


class MissingConfigFilesError(CollectException):
    pass


class NoBasicTypeException(CollectException):
    pass


def collect_defines(directory):
    
    config = {}
    cache_file = os.path.join(directory, bssettings.CFG_CACHEFILE)
    usr_file = os.path.join(directory, bssettings.CFG_USERFILE)
    
    if ((not os.path.isfile(cache_file))
            or (not os.path.isfile(usr_file))):
        raise MissingConfigFilesError()
    else:
        f = open(cache_file, 'r')
        try:
            pick = cPickle.Unpickler(f)
            config = pick.load()
        finally:
            f.close()
        
        f = open(usr_file, 'r')
        try:
            pick = cPickle.Unpickler(f)
            ucfg = pick.load()
        finally:
            f.close()
        
        config.update(ucfg)
        
        return config


def prepare_define(value):
    
    if isinstance(value, types.StringTypes):
        return value
    elif isinstance(value, types.BooleanType):
        return '1' if value else '0'
    elif (isinstance(value, types.IntType) or 
            isinstance(value, types.LongType) or
            isinstance(value, types.FloatType)):
        return str(value)
    else:
        raise NoBasicTypeException


def output_define(key, value, all=False):
    
    try:
        dvalue = prepare_define(value)
        print '-D"%s=%s"' % (key, dvalue),
    except NoBasicTypeException:
        if all:
            if (isinstance(value, types.TupleType) or 
                    isinstance(value, types.ListType)):
                for (index, v) in enumerate(value):
                    output_define(key + "_%d" % index, v, all=all)
            elif isinstance(value, types.DictType):
                
                for (k, v) in value.iteritems():
                    strkey = str(k)
                    output_defines(key + strkey, v, all=all)


def main(args):
    
    parser = optparse.OptionParser(
        usage="usage: %prog def [options] path")
    
    parser.add_option("-v", "--verbose", action="store_true",
        help="turns on warnings (to stderr)...")
    
    parser.add_option("-a", "--all", action="store_true",
        help="shows all defines (even dictonaries or python stuff)")
    
    parser.set_defaults(verbose=False, all=False)
    
    options, args = parser.parse_args(args)
    
    if len(args) < 2:
        parser.print_help(file=sys.stderr)
        sys.exit(1)
    else:
        if os.path.isdir(args[1]):
            path = args[1]
        else:
            path = os.path.split(args[1])[0]
    
    config = collect_defines(path)
    
    for (dkey, value) in config.iteritems():
        output_define(dkey, value, all=options.all)
