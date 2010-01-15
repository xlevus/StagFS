#    Copyright (C) 2009  Chris Targett  <chris@xlevus.net>
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

import re
import logging
import os.path
import simplejson as json
import stat
import time
import copy

import stag.fs
import stag.utils

class FilePath(stag.fs.LinkNode):
    """
    Contains the reference to the actual file or folder
    and represents it as a symlink.

    This could be improved to provide the actual file as
    opposed to symlink to it.
    """
    def __init__(self, link):
        self.link = link
        self.isdir = os.path.isdir(link)
        self.isfile = not self.isdir
    
    def __str__(self):
        return self.link
    
    def __repr__(self):
        return "<FilePath '%s'>" % self.__str__()

class Tag(stag.fs.DirectoryNode):
    """
    Represents a tag. Contains a dictionary of
        "filename": FilePath()
    i.e.
    {
        "2001 A Space Odyssey (1968)": <FilePath '/home/media/2001 A Space Odyssey (1968)/'>,
        "Blade Runner (1982)": <FilePath '/home/media/Blade Runner (1982)/'>,
    }
    """
    def add_file(self, file_path):
        # Add a file to the tag.
        basename = os.path.basename(file_path.link)
        self[basename] = file_path
    
    def __repr__(self):
        return "<Tag>"

class TagSet(stag.fs.DirectoryNode):
    """
    Represents a set of tags. Contains a dictionary of
        "tag-name": Tag()

    i.e, for the 'director' tag-set
    {
        "Stanley Kubrick": <Tag>,
        "Ridley Scott": <Tag>,
    }
    """

    def add_tags(self, tags, file_path):
        """
        Adds tag(s) to the set and assigns files to that tag.
        """
        if isinstance(tags, (str, unicode, int)):
            # Single tag
            tags = unicode(tags)
            self.setdefault(tags,Tag()).add_file(file_path)

        elif isinstance(tags, (dict,)):
            # Nested tag sets are unsupported
            pass

        else:
            # Multiple tags
            for tag in tags:
                self.setdefault(tag,Tag()).add_file(file_path)
    
    def __repr__(self):
        return "<TagSet>"

class DataType(stag.fs.DirectoryNode):
    """
    Represents the data type of the tags. This is
    the 2nd level of the filesystem.

    i.e, for the 'movie' data type
    {
        'director': <TagSet>,
        'year': <TagSet>,
    }
    """
    def add_tag_set(self, name):
        return self.setdefault(name, TagSet())
    
    def __repr__(self):
        return "<DataType>"

class RootNode(stag.fs.DirectoryNode):
    """
    Walks the source directory looking for .stag files and
    creates a tree of stag.fs.Nodes representing the final FS.

    Contains a dictionary of data-type-name: DataType()
    i.e.
    {
        'movie': <DataType>,
        'TV': <DataType>,
    }
    """

    def __init__(self, *dirs):
        for dir in dirs:
            os.path.walk(dir, self.find_data_containers, None)

    def find_data_containers(self, arg, directory, contents):
        func = stag.utils.curry(os.path.join, directory)
        for file in map(func, contents):
            if file.endswith('.stag'):
                self.load_data(file)

    def load_data(self, container_path):
        """
        Loads the .stag files and turns them into stag.fs.Node objects
        """
        data = json.load(open(container_path, 'r'))
       
        data_type = self.setdefault(data['data_type'], DataType())
        
        file_root = os.path.dirname(os.path.abspath(container_path))

        # Iterate through the define files.
        for filename, data in data['files'].iteritems():
            if filename == '.': # tags are for the folder not its contents
                filename = file_root
            else:
                filename = os.path.join(file_root, filename)

                # Avoid creating dead links
                if not os.path.exists(filename):
                    continue
           
            file_path = FilePath(filename)
        
            for tag_set, tags in data.iteritems():
                ts = data_type.add_tag_set(tag_set) # Add the TagSet to the DataType
                ts.add_tags(tags, file_path)        # Add the tags to the tag-set

