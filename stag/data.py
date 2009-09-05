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
    def __init__(self, link):
        self.link = link
        self.isdir = os.path.isdir(link)
        self.isfile = not self.isdir
    
    def __str__(self):
        return self.link
    
    def __repr__(self):
        return "<FilePath '%s'>" % self.__str__()

class Tag(stag.fs.DirectoryNode):
    def add_file(self, file_path):
        basename = os.path.basename(file_path.link)
        self[basename] = file_path

class TagSet(stag.fs.DirectoryNode):
    def add_tags(self, tags, file_path):
        if stag.utils.isiter_not_string(tags):
            for tag in tags:
                self.setdefault(tag,Tag()).add_file(file_path)
        else:
            self.setdefault(tags,Tag()).add_file(file_path)

class DataType(stag.fs.DirectoryNode):
    def add_tag_set(self, name):
        return self.setdefault(name, TagSet())

class RootNode(stag.fs.DirectoryNode):

    def __init__(self, *dirs):
        for dir in dirs:
            os.path.walk(dir, self.find_data_containers, None)

    def find_data_containers(self, arg, directory, contents):
        pass
        func = stag.utils.curry(os.path.join, directory)
        for file in map(func, contents):
            if file.endswith('.stag'):
                self.load_data(file)

    def load_data(self, container_path):
        data = json.load(open(container_path, 'r'))
       
        data_type = self.setdefault(data['data_type'], DataType())
        
        file_root = os.path.dirname(os.path.abspath(container_path))
        for filename, data in data['files'].iteritems():    
            if filename == '.':
                filename = file_root
            else:
                filename = os.path.join(file_root, filename)

            for tag_set, tags in data.iteritems():
                file_path = FilePath(filename)
                data_type.add_tag_set(tag_set).add_tags(tags, file_path)

