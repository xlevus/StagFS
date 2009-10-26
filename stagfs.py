#!/usr/bin/env python

#    Copyright (C) 2009  Chris Targett  <chris@xlevus.net>
#
#    This file is part of StagFS.
#
#    StagFS is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    StagFS is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with StagFS.  If not, see <http://www.gnu.org/licenses/>.
#

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

        self.parser.add_option('--source-dir', dest='source_dir', metavar='dir')
        self.parse(errex=1)
        opts, args = self.cmdline

        if opts.source_dir == None:
            print "Error: Missing source directory option. See --help for more info."
            sys.exit()

        self.root_node = stag.data.RootNode(opts.source_dir)
        
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
    fs.main()
    
