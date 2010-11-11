import os.path
import simplejson


import db

class BaseLoader(object):
    def __init__(self, source_file):
        self.cursor = db.CursorWrapper()

        for datatype, filename, data in self.get_data(source_file):
            self.create(datatype, source_file, filename, data)
            self.cursor.commit()

    def create(self, datatype, source_file, target_file, data, parent=None):
        if isinstance(data, dict):
            self.create_from_dict(datatype, source_file, target_file, data, parent)
        elif isinstance(data, (list, tuple)):
            self.create_from_list(datatype, source_file, target_file, data, parent)
        elif isinstance(data, (str, unicode)):
            self.create_reference(datatype, source_file, target_file, parent)

    def create_from_dict(self, datatype, source_file, target_file, data, parent=None):
        for tag, data in data.iteritems():
            new_parent = self.create_tag(datatype, tag, parent)
            self.create(datatype, source_file, target_file, data, new_parent)

    def create_from_list(self, datatype, source_file, target_file, data, parent=None):
        for tag in set(data):
            new_parent = self.create_tag(datatype, tag, parent)
            self.create_reference(datatype, source_file, target_file, new_parent)

    def create_reference(self, datatype, source_file, target_file, parent=None):
        part = os.path.basename(target_file)
        select = self.cursor("""SELECT id FROM stagfs WHERE parent IS ? AND (realfile = ? OR part = ?)""",
                (parent, target_file, part)).fetchone()
        if not select:
            insert = self.cursor("""INSERT INTO stagfs (datatype, parent, part, realfile, source) VALUES (?,?,?,?,?)""",
                (datatype, parent, part, target_file, source_file))

    def create_tag(self, datatype, name, parent=None):
        select = self.cursor("""SELECT id FROM stagfs WHERE parent IS ? AND part = ?""", (parent, name)).fetchone()
        if select:
            return select[0]
        else:
            insert = self.cursor("""INSERT INTO stagfs (datatype, parent, part, realfile, source) VALUES (?, ?, ?, ?, ?)""", 
                (datatype, parent, name, "", ""))
            return insert.lastrowid

    def get_data(self, filename):
        """
        data should return an iterable of:
            (data_type, absolute_file_name, data_structure)

        There is no need to check for nonexistant files as this will be done later by StagFS.
        """
        pass

class StagfileLoader(BaseLoader):
    def get_data(self, filename):
        with open(filename, 'r') as container:
            data = simplejson.load(container)
        
        file_root = os.path.dirname(os.path.abspath(filename))
        data_type = data['data_type']

        for filename, data in data['files'].iteritems():
            if filename == '.':
                filename = file_root
            else:
                filename = os.path.join(file_root, filename)

            yield (data_type, filename, data)

