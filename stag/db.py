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

import sqlite3
import logging

logger = logging.getLogger('stagfs.db')

DB_FILE = 'stagfs.sqlite'

CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS stagfs ( 
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        datatype VARCHAR(25) NOT NULL,
        parent INTEGER REFERENCES stagfs (id),
        part VARCHAR(50) DEFAULT "" NOT NULL,
        realfile VARCHAR(255) DEFAULT NULL,
        source TEXT DEFAULT "" NOT NULL
    );
"""


class CursorWrapper(object):
    """
    Wrapper around sqlite3.connect() and sqlite3.cursor(). Assures
    that each connection talks to the same place, and creates the
    table if it's needed.

    If locking is needed, it will be implemented here.
    """
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.execute(CREATE_TABLE)
        self.conn.commit()

    def __call__(self, *args, **kwargs):
        cursor = self.conn.cursor()
        cursor.execute(*args, **kwargs)
        return cursor

    def commit(self):
        return self.conn.commit()
