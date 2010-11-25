#    Copyright (C) 2010  Chris Targett  <chris@xlevus.net>
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
import stat
import errno
import logging

import fuse
fuse.fuse_python_api = (0,2)

logger = logging.getLogger('stagfs.fuse')

import stag.db
import stag.data
import stag.views
import stag.loaders

TEMP_CONFIG = {
    # I think fuse dicks with paths so they need to be absolute.
    'db_name': os.path.abspath(os.path.join(__file__, '../../stagfs.sqlite')), 
    'source_folders': ('test_source',),
    'loaders': (('stag', stag.loaders.StagfileLoader),)
}

class StagFuse(fuse.Fuse):
    def __init__(self, *args, **kw):
        fuse.Fuse.__init__(self, *args, **kw)
         
        #self.parser.add_option('--config', dest='config_file', metavar='file', default=None)
        self.parse(errex=1)
        opts, args = self.cmdline

        self.data = stag.data.DataManager(
            db_name = TEMP_CONFIG['db_name'],
            source_folders = TEMP_CONFIG['source_folders'],
            loaders = TEMP_CONFIG['loaders'],
        )
        self.data.load_initial()

        self.view_manager = stag.views.ViewManager(TEMP_CONFIG['db_name'])

        logger.debug('Fuse init complete.')

    def fsinit(self):
        self.data.start()

    def getattr(self, path):
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

        logger.debug('getattr %r' % path)


        stat_obj = fuse.Stat()
        stat_obj.st_mode = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
        stat_obj.st_ino = 0
        stat_obj.st_dev = 0
        stat_obj.st_nlink = 0
        stat_obj.st_uid = os.getuid()
        stat_obj.st_gid = os.getgid()
        stat_obj.st_size = 0
        
        contents = self.view_manager.get(path)
        if contents is None:
            return -errno.ENOENT
        
        if isinstance(contents, list):
            stat_obj.st_mode = stat_obj.st_mode | stat.S_IFDIR

        return stat_obj

    def readdir(self, path, offset):
        """
        return: [[('file1', 0), ('file2', 0), ... ]]
        """

        logger.debug('readdir %r %r' % (path, offset))
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')

    def mythread(self):
        logger.debug('mythread')
        return -errno.ENOSYS

    def chmod(self, path, mode):
        logger.debug('chmod %r %r' % (path, oct(mode)))
        return -errno.ENOSYS

    def chown(self, path, uid, gid):
        logger.debug('chown %r %r %r' % (path, uid, gid))
        return -errno.ENOSYS

    def fsync(self, path, isFsyncFile):
        logger.debug('fsync %r %r' % (path, isFsyncFile))
        return -errno.ENOSYS

    def link(self, targetPath, linkPath):
        logger.debug('link %r %r' % ( targetPath, linkPath))
        return -errno.ENOSYS

    def mkdir(self, path, mode):
        logger.debug('mkdir %r %r' % (path, oct(mode)))
        return -errno.ENOSYS

    def mknod(self, path, mode, dev):
        logger.debug('mknod %r %r %r' % (path, oct(mode), dev))
        return -errno.ENOSYS

    def open(self, path, flags):
        logger.debug('open %r %r' % (path, flags))
        return -errno.ENOSYS

    def read(self, path, length, offset):
        logger.debug('read %r %r %r' % (path, length, offset))
        return -errno.ENOSYS

    def readlink(self, path):
        logger.debug('readlink %r' % path)
        return -errno.ENOSYS

    def release(self, path, flags):
        logger.debug('release %r %r' % (path, flags))
        return -errno.ENOSYS

    def rename(self, oldPath, newPath):
        logger.debug('rename %r %r' % (oldPath, newPath))
        return -errno.ENOSYS

    def rmdir(self, path):
        logger.debug('rmdir %r' % path)
        return -errno.ENOSYS

    def statfs(self):
        logger.debug('statfs')
        return -errno.ENOSYS

    def symlink(self, targetPath, linkPath):
        logger.debug('symlink %r %r' % (targetPath, linkPath))
        return -errno.ENOSYS

    def truncate(self, path, size):
        logger.debug('truncate %r %r' % (path, size))
        return -errno.ENOSYS

    def unlink(self, path):
        logger.debug('unlink %r' % path)
        return -errno.ENOSYS

    def utime(self, path, times):
        logger.debug('utime %r %r' % (path, times))
        return -errno.ENOSYS

    def write(self, path, buf, offset):
        logger.debug('write %r %r %r' % (path, buf, offset))
        return -errno.ENOSYS

