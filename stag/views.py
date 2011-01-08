import logging

from fuse import Directory
from stag import StagException
from stag.db import ConnectionWrapper

logger = logging.getLogger('stagfs.views')

class DoesNotExist(StagException):
    pass

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

    def get_datatypes(self):
        conn = ConnectionWrapper(self.db_name)
        result = conn.execute("SELECT DISTINCT datatype FROM stagfs WHERE parent IS NULL")
        return [x[0] for x in result]
    
    def get(self, path):
        if path == '/':
            return self.get_root()
        
        # Extract datatype from the path (the first component) and 
        # forward the new
        parts = path.split('/')
        prefix = parts[1] 
        if self.views.has_key(prefix):
            view = self.views[prefix]
        else:
            if prefix not in self.get_datatypes():
                raise DoesNotExist("/%s has no associated datatype or view." % prefix)
            view = self.views.setdefault(prefix, View(prefix, self.db_name))
        return view.get('/'.join(['']+parts[2:]))

    def get_root(self):
        """
        Gets the root folder of the FS. This should be a combination of registered
        views and datatypes.
        """
        # TODO: Add mechanism allow /someview/ to consume some_other_datatype
        output = set(self.views.keys())
        output.update(self.get_datatypes())
        return output

class View(object):
    def __init__(self, datatype, db_name):
        self.db_name = db_name
        self.datatype = datatype

    def get(self, path, parent=None, conn=None):
        logger.debug("GET: %r, %r" % (path, parent))

        if conn is None:
            conn = ConnectionWrapper(self.db_name)

        if path and path[0] == '/': # Clean out opening / to make recursion easier
            path = path[1:]

        if path == '':
            result = conn.execute("SELECT part FROM stagfs WHERE datatype = ? AND parent IS ?", (self.datatype,parent))
            return set([row[0] for row in result])
        else:
            parts = path.split('/')
            while parts:
                sql = ("SELECT id FROM stagfs WHERE datatype = ? AND parent IS ? AND part = ?", (self.datatype, parent, parts[0]))
                result = conn.execute(*sql).fetchone()
                logger.debug("GET SQL: %r %r" % sql)
                return self.get("/".join(parts[1:]), result[0], conn)
