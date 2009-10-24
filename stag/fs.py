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

import os
import logging
import time
import stat

import fuse

class Stat(fuse.Stat):
    """Base stat class, adds read perms and a/c/mtimes"""
    st_mode = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
    st_ino = 0
    st_dev = 0
    st_nlink = 0
    st_uid = os.getuid()
    st_gid = os.getgid()
    st_size = 0

    def __init__(self):
        self.st_atime = self.st_mtime = self.st_ctime = time.time()

class LinkStat(Stat):
    """Stat class for links"""
    st_mode = stat.S_IFLNK | Stat.st_mode

class DirectoryStat(Stat):
    """Stat class for directories"""
    st_mode = stat.S_IFDIR | Stat.st_mode
    st_nlink = 1

class Node(object):
    def _attr(self):
        return Stat()
    attr = property(_attr)
    
    def getNode(self, path):
        return self

class LinkNode(Node):
    def __init__(self, link):
        self.link = link

    def _attr(self):
        return LinkStat()
    attr = property(_attr)

class DirectoryNode(dict, Node):
    def _attr(self):
        return DirectoryStat()
    attr = property(_attr)
    
    def getNode(self, path):
        if path == os.sep:
            return self
        else:
            path = path[1:]
            p2 = path.split(os.sep,1)
            if len(p2) == 1:
                p2.append('')
            if self.has_key(p2[0]):
                return self[p2[0]].getNode(os.sep+p2[1])
        
    def contents(self):
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')
    
        for k in self.keys():
            try:
                yield fuse.Direntry(str(k))
            except UnicodeEncodeError:
                logging.warn("Unable to enode '%s'" % k)

