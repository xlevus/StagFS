from stag.db import ConnectionWrapper

class ViewManager(object):
    def __init__(self, db_name):
        self.db_name = db_name 
    
    def get(self, path):
        if path == '/':
            return self.get_root()

    def get_root(self):
        conn = ConnectionWrapper(self.db_name)
        result = conn.execute("SELECT DISTINCT datatype FROM stagfs WHERE parent IS NULL")
        datatypes = []
        for row in result:
            datatypes.append(row[0])
        return datatypes
