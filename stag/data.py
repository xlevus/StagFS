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
import logging
import threading
import inotifyx

import stag.db
import stag.utils

logger = logging.getLogger('stagfs.data')

class DataManager(threading.Thread):
    def __init__(self, db_name, source_folders, loaders):
        super(DataManager, self).__init__()

        self.loaders = loaders
        self.db_name = os.path.abspath(db_name)
        self.source_folders = map(os.path.abspath, source_folders)
 
    def load_initial(self):
        conn = stag.db.ConnectionWrapper(self.db_name)
        logger.debug("Clearing stagfs table")
        conn.execute("DELETE FROM stagfs WHERE 1")

        for dir in self.source_folders:
            self.process_dir(dir, conn)

    def start(self, exit_event):
        self.exit_event = exit_event
        self.fd = inotifyx.init()
        self.wd_list = {}

        events = inotifyx.IN_CREATE | inotifyx.IN_DELETE | inotifyx.IN_MODIFY | \
                inotifyx.IN_MOVED_TO | inotifyx.IN_MOVED_FROM
        for path in self.source_folders:
            path = os.path.abspath(path)
            try:
                self.wd_list[inotifyx.add_watch(self.fd, path, events)] = path
            except Exception, e:
                logger.error("Failed to setup inotify watch on '%s'. Reason: %r" % (path, e))

        super(DataManager, self).start()
    
    def run(self):
        while not self.exit_event.isSet():
            # Setting a significant timeout here will make the FS unmountable
            # Instead use a short timeout on get_events and sleep afterwards
            events = inotifyx.get_events(self.fd, 0.1)
            for e in events:
                try:
                    e.name = os.path.join(self.wd_list[e.wd], e.name) # Normalise event name
                    logger.debug("Inotify Event: %r" % e)
                    if e.mask & (inotifyx.IN_DELETE | inotifyx.IN_MOVED_FROM | inotifyx.IN_MODIFY):
                        self.handle_delete(e)
                    if e.mask & (inotifyx.IN_CREATE | inotifyx.IN_MOVED_TO | inotifyx.IN_MODIFY):
                        self.handle_create(e)
                except Exception, e:
                    logger.error("Thread Error: %r" % e)

            time.sleep(5)
       
        for wd in self.wd_list.keys():
            rm_watch(self.fd, wd)
        os.close(self.fd)
    
    def process_dir(self, dir, conn=None):
        for root, dirs, files in os.walk(dir):
            for f in files:
                self.process_file(os.path.join(root, f), conn)

    def process_file(self, source_file, conn=None):
        for extension, loader in self.loaders:
            if source_file.endswith("."+extension):
                logger.debug("Found %r. Loading with %r" % (source_file, loader))

                if conn is None:
                    conn = stag.db.ConnectionWrapper(self.db_name)

                loader(conn, source_file)

    def process_path(self, path):
        """Utility function to process either a folder or a directory"""
        if os.path.isfile(path):
            self.process_file(path)
        elif os.path.isdir(path):
            self.process_dir(path)
      
    def handle_delete(self, event):
        conn = stag.db.ConnectionWrapper(self.db_name)
        conn.execute(
            "DELETE FROM stagfs WHERE source = ?",
            (event.name,)
        )

    def handle_create(self, event):
        self.process_path(event.name)

