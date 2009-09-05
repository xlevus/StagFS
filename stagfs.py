#!/usr/bin/env python

import re
import optparse
import os
import stat
import errno
import logging
import simplejson as json
from optparse import OptionParser

import fuse
fuse.fuse_python_api = (0,2)

import stag.fs
import stag.data

import sys
 
def setUpLogging():
    def exceptionCallback(eType, eValue, eTraceBack):
        import cgitb
 
        txt = cgitb.text((eType, eValue, eTraceBack))
 
        logging.fatal(txt)
    
        # sys.exit(1)
 
    # configure file logger
    logging.basicConfig(level = logging.DEBUG,
                        format = '%(asctime)s %(levelname)s %(message)s',
                        filename = '/tmp/stagfs.log',
                        filemode = 'a')
    
    # configure console logger
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setLevel(logging.DEBUG)
    
    consoleFormatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    consoleHandler.setFormatter(consoleFormatter)
    logging.getLogger().addHandler(consoleHandler)
 
    # replace default exception handler
    sys.excepthook = exceptionCallback
    
    logging.debug('Logging and exception handling has been set up')

class StagFS(fuse.Fuse):
    def __init__(self, *args, **kwargs):
        fuse.Fuse.__init__(self, *args, **kwargs)

        self.parser.add_option('-i', '--items-dir', dest='items_dir', metavar='dir')
        self.parse()
        opts, args = self.cmdline

        self.root_node = stag.data.RootNode(opts.items_dir)
        
    def getNode(self, path):
        return self.root_node.getNode(path)

    def getattr(self, path):
        node = self.getNode(path)

        if node is None:
            return -errno.ENOENT

        return node.attr

    def readdir(self, path, offset):
        node = self.getNode(path)
        return node.contents()

    def readlink(self, path):
        node = self.getNode(path)
        if node == None:
            return -errno.ENOENT
        return node.link

if __name__ == '__main__':
    setUpLogging()

    fs = StagFS()
    opts, args = fs.cmdline
    
    if opts.items_dir == None:
        fs.parser.print_help()
        print "Error: Missing directory option"
        sys.exit()

    fs.main()
    
