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

import stag.db
import stag.utils

logger = logging.getLogger('stagfs.data')

class DataManager(threading.Thread):
    def __init__(self, db_name, source_folders, loaders):
        super(DataManager, self).__init__()

        self.db_name = db_name
        self.source_folders = source_folders
        self.loaders = loaders
    
    def run(self):
        pass
    
    def load_initial(self):
        conn = stag.db.ConnectionWrapper(self.db_name)
        logger.debug("Clearing stagfs table")
        conn.execute("DELETE FROM stagfs WHERE 1")

        for dir in self.source_folders:
            os.path.walk(dir, self.process_folder, conn)
     
    def process_folder(self, conn, directory, contents):
        func = stag.utils.curry(os.path.join, directory)
        for source_file in map(func, contents):
            for extension, loader in self.loaders:
                if source_file.endswith("."+extension):
                    logger.debug("Found %r. Loading with %r" % (source_file, loader))
                    loader(conn, source_file)
       
