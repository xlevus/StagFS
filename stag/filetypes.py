import os
import stat
import errno
import logging

from fuse import Stat

logger = logging.getLogger('stagfs.filetypes')

class StagFile(object):
    """
    Base class for all 'files' in StagFS. Subclasses should provide/override
    all Fuse functions where relevant.
    """

    def getattr(self):
        """
        - st_mode (protection bits)
        - st_ino (inode number)
        - st_dev (device)
        - st_nlink (number of hard links)
        - st_uid (user ID of owner)
        - st_gid (group ID of owner)
        - st_size (size of file, in bytes)
        - st_atime (time of most recent access)
        - st_mtime (time of most recent content modification)
        - st_ctime (platform dependent; time of most recent metadata change on Unix,
                    or the time of creation on Windows).
        """
        stat_obj = Stat()
        stat_obj.st_mode = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
        stat_obj.st_ino = 0
        stat_obj.st_dev = 0
        stat_obj.st_nlink = 0
        stat_obj.st_uid = os.getuid()
        stat_obj.st_gid = os.getgid()
        stat_obj.st_size = 0

        return stat_obj


class VirtualDirectory(StagFile):
    """
    Represents a directory within StagFS. Has no real life counterpart.
    """
    def __init__(self, contents):
        self._contents = contents

    def readdir(self):
        return [x.encode('ascii','replace') for x in self._contents]
           
    def getattr(self):
        stat_obj = super(VirtualDirectory, self).getattr()
        stat_obj.st_mode = stat_obj.st_mode | stat.S_IFDIR
        return stat_obj


class RealFile(StagFile):
    """
    A file in StagFS that points to a real file on disk.
    """
    def __init__(self, target):
        logger.debug("New RealFile -> %r" % target)
        if not os.path.exists(target):
            from stag.views import DoesNotExist
            raise DoesNotExist(target)
        self._target = target
    
    def getattr(self, *args):
        logger.debug("GETATTR: args %r" % (args,))
        file_stat = os.stat(self._target)
        stat_obj = Stat()

        stat_obj.st_mode = file_stat[0]
        stat_obj.st_ino = file_stat[1]
        stat_obj.st_dev = file_stat[2]
        stat_obj.st_nlink = file_stat[3]
        stat_obj.st_uid = file_stat[4]
        stat_obj.st_gid = file_stat[5]
        stat_obj.st_size = file_stat[6]
        stat_obj.st_atime = file_stat[7]
        stat_obj.st_mtime = file_stat[8]
        stat_obj.st_ctime = file_stat[9]
    
        return stat_obj

    def readdir(self):
        if not os.path.isdir(self._target):
            return -errno.ENOTDIR
        return os.listdir(self._target)

class SymlinkRealFile(RealFile):
    """
    Represents real files as symlinks.
    Stopgap measure, but it's a lot easier to deal with code wise.
    """

    def getattr(self, *args):
        logger.debug("GETATTR: args %r" % (args,))
        stat_obj = Stat()
        stat_obj.st_mode = stat.S_IFLNK | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
        stat_obj.st_ino = 0
        stat_obj.st_dev = 0
        stat_obj.st_nlink = 0
        stat_obj.st_uid = os.getuid()
        stat_obj.st_gid = os.getgid()
        stat_obj.st_size = 0

        return stat_obj

    def readlink(self):
        logger.debug("READLINLK %s" % self._target)
        return str(self._target)

