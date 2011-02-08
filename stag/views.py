import os
import logging

from stag import filetypes
from stag import StagException
from stag.db import ConnectionWrapper

logger = logging.getLogger('stagfs.views')

class DoesNotExist(StagException):
    """Exception for when Fuse requests a path that does not exist."""
    pass

class Dispatcher(object):
    def __init__(self, db_name):
        self.db_name = db_name
        self.views = {}

        conn = ConnectionWrapper(self.db_name)
        result = conn.execute("SELECT DISTINCT datatype FROM stagfs WHERE parent IS NULL")
        for row in result:
            self.views[row[0]] = View(row[0])

    def get(self, path):
        if path == '/':
            return self.get_root()

        split = path.split(os.sep)
        datatype = split[1]
        return self.get_view(split[1]).get(os.sep + os.sep.join(split[2:]), self.db_name)

    def get_root(self):
        return filetypes.VirtualDirectory(contents=self.views.keys())
        
    def get_view(self, datatype):
        try:
            return self.views[datatype]
        except KeyError:
            raise DoesNotExist("No view associated with datatype %r" % datatype)

class View(object):
    def __init__(self, datatype):
        self.datatype = datatype

    def get(self, path, db_name):
        conn = ConnectionWrapper(db_name)
        path = path.split(os.sep)[1:] # Root: ''; /Path/Somewhere: '','Path','Somewhere'
        realfile = None
        parent_id = None

        while len(path) > 0 and path != ['']:
            try:
                parent_id, realfile = conn.execute(
                        "SELECT id,realfile FROM stagfs WHERE datatype = ? AND parent IS ? AND part = ?",
                        (self.datatype, parent_id, path[0])
                ).fetchone()
                path = path[1:]
            except TypeError:
                # No helpful data here to output meaningful error message
                raise DoesNotExist("Could not find path") 

        if not realfile:
            result = conn.execute("SELECT part FROM stagfs WHERE datatype = ? AND parent IS ?", 
                    (self.datatype,parent_id))
            return filetypes.VirtualDirectory(contents=[x[0] for x in result])
        else:
            return filetypes.RealFile(target=realfile)

