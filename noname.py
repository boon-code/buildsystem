#! /usr/bin/env python
# -*- coding: utf-8 -*-
# my build system
import sys
import os
import optparse

DEBUG_ = True

import bsconfig
import bsdef
import bseval


def main():
    
    args = sys.argv[1:]
    
    if len(args) >= 1:
        basedir = os.path.split(sys.argv[0])[0]
        
        if args[0] == 'cfg':
            return bsconfig.main(args)
        elif args[0] == 'def':
            return bsdef.main(args)
        elif args[0] == 'eval':
            return bseval.main(args)
    
    #else:
    
    parser = optparse.OptionParser(
        usage="usage: %prog sub-command [options]",
        epilog="sub-command must be either 'cfg', 'def' or 'eval'")
    
    parser.add_option("-V", "--version", action="store_true",
        dest="version", help="shows version number only...")
    
    parser.set_defaults(version=False)
    
    options, args_dont_use = parser.parse_args(args)
    
    if options.version:
        print "noname-build-system version %s" % bssettings.VERSION
        return


if __name__ == '__main__':
    main()
