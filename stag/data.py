import re
import logging
import os.path
import simplejson as json
import stat
import time

import stag.fs
import stag.utils

class FilePath(stag.fs.LinkNode):
    def __init__(self, link):
        logging.debug("found file '%s'" % link)
        self.link = link
        self.isdir = os.path.isdir(link)
        self.isfile = not self.isdir
    
    def __str__(self):
        return self.link
    
    def __repr__(self):
        return "<FilePath '%s'>" % self.__str__()

class TagSet(stag.fs.DirectoryNode):
    def add_tags(self, tags, file_path):
        if stag.utils.isiter_not_string(tags):
            for tag in tags:
                self.setdefault(tag,[]).append(file_path)
        else:
            self.setdefault(tags,[]).append(file_path)

class DataType(stag.fs.DirectoryNode):
    def add_tag_set(self, name):
        return self.setdefault(name, TagSet())

class DataRoot(stag.fs.DirectoryNode):
    stagfile_re = re.compile('.*\.stag$')
    stagfiles = []

    def __init__(self, dir):
        dir = os.path.abspath(dir)
        os.path.walk(dir, self.find_stagfiles, None)
        map(self.parse_file, self.stagfiles)

    def add_data_type(self, name):
        """"""
        return self.setdefault(name, DataType())
     
    def find_stagfiles(self, arg, dirname, names):
        func = stag.utils.curry(os.path.join, dirname)
        self.stagfiles.extend( map(func, filter(self.stagfile_re.findall, names)))
   
    def parse_file(self, file):
        logging.debug("Parsing stagfile '%s'" % file)
        file_root = os.path.dirname(file)
        data = json.load(open(file, 'r'))
    
        datatype = self.add_data_type(data['data_type'])
    
        for filename, data in data['files'].iteritems():
            if filename == '.':
                filename = file_root
    
        file_path = FilePath(filename)
        for tag_set, tags in data.iteritems():
            datatype.add_tag_set(tag_set).add_tags(tags, file_path)

