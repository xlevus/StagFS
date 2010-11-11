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
    Wrapper around sqlite3.connect() and sqlite3.cursor().
    If needed, locking will be implemented here.
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
