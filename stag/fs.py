import os
import logging
import time
import stat

import fuse

class Stat(fuse.Stat):
    st_mode = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
    st_ino = 0
    st_dev = 0
    st_nlink = 0
    st_uid = 0
    st_gid = 0
    st_size = 0

    def __init__(self):
        self.st_atime = self.st_mtime = self.st_ctime = time.time()

class LinkStat(Stat):
    st_mode = stat.S_IFLNK | Stat.st_mode

class DirectoryStat(Stat):
    st_mode = stat.S_IFDIR | Stat.st_mode
    st_nlink = 2

class Node(object):
    def __init__(self):
        pass

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

class DirectoryNode(Node, dict):
    def __init__(self):
        pass

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
            yield fuse.Direntry(k)
