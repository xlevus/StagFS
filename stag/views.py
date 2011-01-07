import logging

from stag.db import ConnectionWrapper

logger = logging.getLogger('stagfs.views')

class ViewManager(object):
    """Manages views and handles the root path"""

    # Views are stored in a dict with the key being the first component
    # of the path. i.e. `/myview/abc/def/` is equivalent to
    # `self.views['myview'].get('/abc/def/')`.

    def __init__(self, db_name, views={}):
        self.db_name = db_name 

        self.views = {}
        for prefix, klass in views.items():
            self.views[prefix] = klass(prefix, self.db_name)
    
    def get(self, path):
        if path == '/':
            return self.get_root()
        
        # Extract datatype from the path (the first component) and 
        # forward the new
        parts = path.split('/')
        datatype = parts[1] 
        view = self.views.setdefault(datatype, View(datatype, self.db_name))
        return view.get('/'.join(['']+parts[2:]))

    def get_root(self):
        """
        Gets the root folder of the FS. This should be a combination of registered
        views and datatypes.
        """
        # TODO: Add mechanism allow /someview/ to consume some_other_datatype
        conn = ConnectionWrapper(self.db_name)
        result = conn.execute("SELECT DISTINCT datatype FROM stagfs WHERE parent IS NULL")
        output = set(self.views.keys())
        for row in result:
            output.add(row[0])
        return output

class View(object):
    def __init__(self, datatype, db_name):
        self.db_name = db_name
        self.datattype = datatype

    def get(self, path, parent=None):
        pass
