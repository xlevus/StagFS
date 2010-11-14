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

import utils
import conf
import db

logger = logging.getLogger('stagfs.data')

class DataManager(threading.Thread):
    def __init__(self, configfile):
        super(DataManager, self).__init__()

        self.settings = conf.Settings(configfile)
    
    def run(self):
        pass
        #while True:
        #    time.sleep(10)
    
    def load_initial(self):
        for dir in self.settings.source_folders:
            os.path.walk(dir, self.process_folder, self.settings.loaders)
     
    def process_folder(self, loaders, directory, contents):
        func = utils.curry(os.path.join, directory)
        for source_file in map(func, contents):
            for extension, loader in loaders:
                if source_file.endswith("."+extension):
                    logger.debug("Found %r. Loading with %r" % (source_file, loader))
                    cursor = db.CursorWrapper(self.settings.db_name)
                    loader(cursor, source_file)
       
