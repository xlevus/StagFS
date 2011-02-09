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
import fcntl
import logging
import itertools
import functools

from threading import Lock

import fuse
fuse.fuse_python_api = (0,2)

logger = logging.getLogger('stagfs.fuse')

import stag.db
import stag.data
import stag.views
import stag.loaders
import stag.filetypes

TEMP_CONFIG = {
    # I think fuse dicks with paths so they need to be absolute.
    'db_name': os.path.abspath(os.path.join(__file__, '../../stagfs.sqlite')), 
    'source_folders': ('test_source',),
    'loaders': (('stag', stag.loaders.StagfileLoader),)
}

def flag2mode(flags):
    md = {os.O_RDONLY: 'r', os.O_WRONLY: 'w', os.O_RDWR: 'w+'}
    m = md[flags & (os.O_RDONLY | os.O_WRONLY | os.O_RDWR)]
    if flags | os.O_APPEND:
        m = m.replace('w', 'a', 1)
    return m

def lock(func):
    """Monitor pattern lock decorator."""
    @functools.wraps(func)
    def inner(self, *args, **kwargs):
        if not hasattr(self, '_lock'):
            self._lock = Lock()
        self._lock.acquire()
        func(self, *args, **kwargs)
        self._lock.release()
    return inner

class StagFile(object):
    def __init__(self, fuse_fs, path, flags, *mode):
        path = fuse_fs.view_manager.get(path)._target
        self.path = path
        self.file = os.fdopen(os.open("." + path, flags, *mode), flag2mode(flags))
        self.fd = self.file.fileno()
        logger.debug("opened %r. Flags: %r Mode: %r" % (path, flags, mode))
    
    @lock
    def read(self, length, offset):
        logger.debug("read on %r. Length: %r Offset: %r" % (self.path, length, offset))
        self.file.seek(offset)
        return self.file.read(length)

    @lock
    def write(self, buf, offset):
        logger.debug("write on %r. Offset: %r" % (self.path, offset))
        self.file.seek(offset)
        self.file.write(buf)
        return len(buf)

    @lock
    def release(self, flags):
        logger.debug("release on %r." % self.path)
        self.file.close()
    
    def _fflush(self):
        if 'w' in self.file.mode or 'a' in self.file.mode:
            self.file.flush()
    
    @lock
    def fsync(self, isfsyncfile):
        logger.debug("fsync on %r. isfsyncfile: %r" % (self.path, isfsyncfile))
        self._fflush()
        if isfsyncfile and hasattr(os, 'fdatasync'):
            os.fdatasync(self.fd)
        else:
            os.fsync(self.fd)

    @lock
    def flush(self):
        logger.debug("flush on %r." % self.path)
        self._fflush()
        os.close(os.dup(self.fd))

    @lock
    def fgetattr(self):
        logger.debug("fgetattr on %r." % self.path)
        return os.fstat(self.fd)

    @lock
    def ftruncate(self, length):
        logger.debug("ftruncate on %r. Length: %r" % (self.path, length))
        self.file.truncate(length)

    @lock
    def lock(self, cmd, owner, **kw):
        logger.debug("lock on %r." % self.path)
        """
        The code here is much rather just a demonstration of the locking
        API than something which actually was seen to be useful.
        
        Advisory file locking is pretty messy in Unix, and the Python
        interface to this doesn't make it better.
        We can't do fcntl(2)/F_GETLK from Python in a platfrom independent
        way. The following implementation *might* work under Linux. 
        #
        if cmd == fcntl.F_GETLK:
            import struct
        
            lockdata = struct.pack('hhQQi', kw['l_type'], os.SEEK_SET,
                                   kw['l_start'], kw['l_len'], kw['l_pid'])
            ld2 = fcntl.fcntl(self.fd, fcntl.F_GETLK, lockdata)
            flockfields = ('l_type', 'l_whence', 'l_start', 'l_len', 'l_pid')
            uld2 = struct.unpack('hhQQi', ld2)
            res = {}
            for i in xrange(len(uld2)):
                 res[flockfields[i]] = uld2[i]
         
            return fuse.Flock(**res)
        
        Convert fcntl-ish lock parameters to Python's weird
        lockf(3)/flock(2) medley locking API...
        """
        op = { fcntl.F_UNLCK : fcntl.LOCK_UN,
               fcntl.F_RDLCK : fcntl.LOCK_SH,
               fcntl.F_WRLCK : fcntl.LOCK_EX }[kw['l_type']]
        if cmd == fcntl.F_GETLK:
            return -EOPNOTSUPP
        elif cmd == fcntl.F_SETLK:
            if op != fcntl.LOCK_UN:
                op |= fcntl.LOCK_NB
        elif cmd == fcntl.F_SETLKW:
            pass
        else:
            return -EINVAL

        fcntl.lockf(self.fd, op, kw['l_start'], kw['l_len'])

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

        self.view_manager = stag.views.Dispatcher(TEMP_CONFIG['db_name'])

        class WrappedStagFile(StagFile):
            def __init__(self2, *args, **kwargs):
                super(WrappedStagFile, self2).__init__(self, *args, **kwargs)
        self.file_class = WrappedStagFile

        logger.debug('Fuse init complete.')

    def fsinit(self):
        self.data.start()
    
    def mythread(self):
        logger.debug('mythread')
        return -errno.ENOSYS

    def getattr(self, path):
        try:
            contents = self.view_manager.get(path)
            return contents.getattr()
        except stag.views.DoesNotExist:
            logger.debug("Path %r not found." % path)
            return -errno.ENOENT

    def readdir(self, path, offset):
        logger.debug('readdir %r %s' % (path, offset))
        resp = self.view_manager.get(path)
        
        for row in itertools.chain([".",".."], resp.readdir()):
            try:
                yield fuse.Direntry(str(row)) # Fuse isn't unicode friendly.
            except UnicodeEncodeError:
                logging.warn("Unable to encode '%s'" % row)

# Lazily create a bunch of attributes
for func_name in ['chmod','chown','link','mkdir','mknod','readlink','rename','rmdir',
        'statfs','symlink','truncate','unlink','utime']:
    def func(self, path, *args, **kwargs):
        logger.debug("%s on %r.   Args:%r   Kwargs:%r" % (func_name, path, args, kwargs))
        try:
            result = self.view_manager.get(path)
            getattr(result, func_name)(*args, **kwargs)
        except AttributeError:
            return -errno.ENOSYS
        except DoesNotExist:
            return -errno.ENOENT
    func.__name__ = func_name
    func.__doc__ = "StagFS.%s - fuse function. See implementations in stag.filetypes" % func_name 
    setattr(StagFuse, func_name, func)

