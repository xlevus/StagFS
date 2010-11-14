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

import os.path
import simplejson

class BaseLoader(object):
    """ Default loader class. Custom loaders should inherit this."""
    # TODO: Tidy up the create_ functions.

    def __init__(self, cursor, source_file):
        self.cursor = cursor

        for datatype, filename, data in self.get_data(source_file):
            self.create(datatype, source_file, filename, data)
            self.cursor.commit()

    def create(self, datatype, source_file, target_file, data, parent=None):
        """Dispatcher for the various create functions"""
        if isinstance(data, dict):
            self.create_from_dict(datatype, source_file, target_file, data, parent)
        elif isinstance(data, (list, tuple)):
            self.create_from_list(datatype, source_file, target_file, data, parent)
        elif isinstance(data, (str, unicode)):
            self.create_reference(datatype, source_file, target_file, parent)

    def create_from_dict(self, datatype, source_file, target_file, data, parent=None):
        """Creates tags for each key in data and then recurses into the value."""
        for tag, data in data.iteritems():
            new_parent = self.create_tag(datatype, tag, parent)
            self.create(datatype, source_file, target_file, data, new_parent)

    def create_from_list(self, datatype, source_file, target_file, data, parent=None):
        """Creates a set of tags from a list and then associates target_file with those tags."""
        # We set() the list here to avoid duplicates. 
        for tag in set(data): 
            new_parent = self.create_tag(datatype, tag, parent)
            self.create_reference(datatype, source_file, target_file, new_parent)

    def create_reference(self, datatype, source_file, target_file, parent=None):
        """Gets or creates a reference to a physical file."""
        # TODO: Account for duplicates
        part = os.path.basename(target_file)
        select = self.cursor("""SELECT id FROM stagfs WHERE parent IS ? AND (realfile = ? OR part = ?)""",
                (parent, target_file, part)).fetchone()
        if not select:
            insert = self.cursor("""INSERT INTO stagfs (datatype, parent, part, realfile, source) VALUES (?,?,?,?,?)""",
                (datatype, parent, part, target_file, source_file))

    def create_tag(self, datatype, name, parent=None):
        """gets or creates a tag in the DB (i.e. a virtual folder)"""
        select = self.cursor("""SELECT id FROM stagfs WHERE parent IS ? AND part = ?""", (parent, name)).fetchone()
        if select:
            return select[0]
        insert = self.cursor("""INSERT INTO stagfs (datatype, parent, part, realfile, source) VALUES (?, ?, ?, ?, ?)""", 
            (datatype, parent, name, "", ""))
        return insert.lastrowid

    def get_data(self, filename):
        """
        data should return an iterable of:
            (data_type, absolute_file_name, data_structure)

        There is no need to check for nonexistant files as this will be done later by StagFS.
        """
        return []

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

