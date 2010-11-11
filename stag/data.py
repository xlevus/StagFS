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
import time
import threading
import logging

from utils import curry
import loaders

logger = logging.getLogger('stagfs.data')

SOURCE_FOLDERS = ['test_source']

class Watcher(threading.Thread):
    def run(self):
        while True:
            logger.debug("Inotify Tick")
            time.sleep(10)

def process_folder(loaders, directory, contents):
    func = curry(os.path.join, directory)
    for source_file in map(func, contents):
        for extension, loader in loaders:
            if source_file.endswith("."+extension):
                logger.debug("Found %r. Loading with %r" % (source_file, loader))
                loader(source_file)

def load_initial():
    for dir in SOURCE_FOLDERS:
        os.path.walk(dir, process_folder, (('stag', loaders.StagfileLoader),))
    
