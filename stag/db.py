import sqlite3

DB_FILE = 'stagfs.sqlite'

CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS stagfs ( 
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent INTEGER REFERENCES stagfs (id),
        part VARCHAR(50) DEFAULT "" NOT NULL,
        realfile VARCHAR(255) DEFAULT NULL,
        source TEXT DEFAULT "" NOT NULL
    );
"""


class DBWrapper(object):
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)

        cursor = conn.cursor()
        cursor.execute(CREATE_TABLE)
        conn.commit()
        cursor.close()

    def get_cursor(self):
        return conn.cursor()

    def release_cursor(self):
        pass
