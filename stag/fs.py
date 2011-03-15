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
import threading
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
        try:
            return func(self, *args, **kwargs)
        finally:
            self._lock.release()
    return inner

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
        
        logger.debug('Fuse init complete.')

    def fsinit(self):
        logger.debug('fsinit')
        self.exit_event = threading.Event()
        self.data.start(self.exit_event)

    def fsdestroy(self):
        self.exit_event.set()
        logger.debug('fsdestroy')
    
    def mythread(self):
        logger.debug('mythread')

    def readdir(self, path, offset):
        logger.debug('readdir %r %s' % (path, offset))
        resp = self.view_manager.get(path)
        
        for row in itertools.chain([".",".."], resp.readdir()):
            try:
                yield fuse.Direntry(str(row)) # Fuse isn't unicode friendly.
            except UnicodeEncodeError:
                logging.warn("Unable to encode '%s'" % row)

    def statfs(self):
        """TODO: Fill this with decent values"""
        return (0,)*10

    def __getattr__(self, name):
        if not name in ['chmod','chown','link','mkdir','mknod','readlink','rename','rmdir', 'symlink','truncate','unlink','utime','getattr']:
            raise AttributeError
        def inner(path, *args, **kwargs):
            logger.debug("%s on %r.   Args:%r   Kwargs:%r" % (name, path, args, kwargs))
            try:
                result = self.view_manager.get(path)
                return getattr(result, name)(*args, **kwargs)
            except AttributeError, e:
                if hasattr(result, name): 
                    # Check that the AttributeError wasn't raised above
                    # if it wasn't, reraise it as it was probably important
                    raise
                return -errno.ENOSYS
            except stag.views.DoesNotExist:
                logger.debug("%r does not exist" % path)
                return -errno.ENOENT
        inner.__name__ = name
        return inner

