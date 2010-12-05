import logging

from stag.db import ConnectionWrapper

logger = logging.getLogger('stagfs.views')

class ViewManager(object):
    def __init__(self, db_name, views={}):
        self.db_name = db_name 

        self.default = View()
        self.views = {}
        for key, value in views.items():
            self.views[key] = value()
    
    def get(self, path):
        if path == '/':
            return self.get_root()
        
        null, view, rest = path.split('/',2)
        return self.views.get(view, self.default).get('/'+rest)

    def get_root(self):
        conn = ConnectionWrapper(self.db_name)
        result = conn.execute("SELECT DISTINCT datatype FROM stagfs WHERE parent IS NULL")
        output = []
        for row in result:
            output.append(row[0])
        return output

class View(object):
    def __init__(self):
        pass

    def get(self, path):
        return []

