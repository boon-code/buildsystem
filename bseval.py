import sys
import os
import optparse
import bssettings
import traceback
import bsdef
import math

def cpp_escape(value):
    value = value.replace('\\', '\\\\')
    value = value.replace('"', '\\"')
    return value


def eval_data(code, env):
    
    try:
        exec(code, env, env)
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
    except Exception:
        sys.stderr.write(traceback.format_exc())
        sys.exit(1)


class EchoHelper(object):
    
    def __init__(self, dst):
        self._dst = dst
    
    def _list_echo(self, text, pre=None, post=None):
        if not (pre is None):
            self._dst.write(str(pre))
        if len(text) > 0:
            for element in text:
                self._dst.write(str(element))
        if not (post is None):
            self._dst.write(str(post))
        self._dst.flush()
    
    def echo(self, *text):
        self._list_echo(text)
    
    def echo_nl(self, *text):
        self._list_echo(text, post='\n')
    
    def str_echo(self, *text):
        text = [cpp_escape(str(i)) for i in text]
        self._list_echo(text, pre='"', post='"')
    
    def str_echo_nl(self, *text):
        text = [cpp_escape(str(i)) for i in text]
        self._list_echo(text, pre='"', post='"\n')


def parse_data(data, dst, env):
    
    echo_obj = EchoHelper(dst)
    env['echo'] = echo_obj.echo
    env['put'] = echo_obj.echo_nl
    env['sput'] = echo_obj.str_echo_nl
    env['secho'] = echo_obj.str_echo
    
    tag = False
    code = ''
    found = True
    
    while found:
        if not tag:
            start_pos = data.find(bssettings.START_TAG)
            if start_pos >= 0:
                if len(data[0:start_pos]) > 0:
                    dst.write(data[0:start_pos])
                tag = True
                data = data[start_pos:]
                code_match = bssettings.CODE_RE.search(data)
                if not (code_match is None):
                    code = ''
                    data = data[code_match.end():]
            else:
                found = False
        
        if tag:
            end_pos = data.find(bssettings.END_TAG)
            if end_pos >= 0:
                tag = False
                if not (code_match is None):
                    code = data[0:end_pos]
                    eval_data(code, env)
                    end_pos += len(bssettings.END_TAG)
                    data = data[end_pos:]
                else:
                    sys.stderr.write("unknown tag...")
            else:
                found = False
                sys.stderr.write("didn't find '?>'")
                sys.exit()
    
    if len(data) > 0:
        dst.write(data)
        dst.flush()

def main(args):
    
    parser = optparse.OptionParser(
        usage="usage: %prog eval [options] file [other files]")
    
    parser.add_option("-o", "--output",
        help="writes output to file 'output'")
    
    parser.add_option("-a", "--auto-output", action="store_true",
        dest="auto", help="automatically outputs bla.xy.in to bla.xy")
    
    parser.add_option("-v", "--verbose", action="store_true",
        help="turns on warnings (to stderr)...")
    
    parser.set_defaults(verbose=False, auto=False)
    
    options, args = parser.parse_args(args)
    
    if len(args) < 2:
        sys.exit(1)
    elif options.output and options.auto:
        sys.stderr.write("you can't set auto and define an output\n")
        sys.stderr.flush()
        sys.exit(1)
    else:
        args = args[1:]
        if options.output:
            if len(args) > 1 and options.verbose:
                sys.stderr.write("since output is set, only the first" +
                    "file will be processed\n")
                sys.stderr.flush()
            args = [args[0]]
    
    for i in args:
        f = open(i, 'r')
        try:
            data = f.read()
        finally:
            f.close()
        
        config = bsdef.collect_defines(os.path.split(i)[0])
                
        env = {'__builtins__' : __builtins__,
            'BS_VERSION' : bssettings.VERSION,
            'math' : math, 'cfg' : config}
        
        if options.output:
            dst = open(options.output, 'w')
            try:
                parse_data(data, dst, env)
            finally:
                dst.close()
        elif options.auto:
            if i.endswith('.in'):
                dst = open(i.rstrip('.in'), 'w')
                try:
                    parse_data(data, dst, env)
                finally:
                    dst.close()
            else:
                dst = open(i + ".pev", 'w')
                try:
                    parse_data(data, dst, env)
                finally:
                    dst.close()
        else:
            dst = sys.stdout
            try:
                parse_data(data, dst, env)
            finally:
                dst.close()

