import re
import optparse
import os.path
import logging
import simplejson as json
from optparse import OptionParser

parser = OptionParser(usage="%prog [options] folder1 folder2 ...", version='0.1')
parser.add_option("--debug", dest="logging_level", action="store_const", const=logging.DEBUG, help="Display debug messages", default=logging.INFO)

def curry(_curried_func, *args, **kwargs):
      def _curried(*moreargs, **morekwargs):
          return _curried_func(*(args+moreargs), **dict(kwargs, **morekwargs))
      return _curried

def isiter_not_string(obj):
    return hasattr(obj, '__iter__') and not isinstance(obj, (str, unicode))

class DataType(dict):
    def add_tag_set(self, name):
        return self.setdefault(name, TagSet())

class TagSet(dict):
    def add_tags(self, tags, file_path):
        if isiter_not_string(tags):
            for tag in tags:
                self.setdefault(tag,[]).append(file_path)
        else:
            self.setdefault(tags,[]).append(file_path)

class FilePath(object):
    def __init__(self, filename):
        self.filename = filename
        self.isdir = os.path.isdir(filename)
        self.isfile = not self.isdir
    
    def __str__(self):
        return self.filename
    
    def __repr__(self):
        return "<FilePath '%s'>" % self.filename

def parse_stagfile(d, stag_file_path):
    logging.debug("Parsing stagfile '%s'" % stag_file_path)

    file_root = os.path.dirname(stag_file_path)
    data = json.load(open(stag_file_path,'r'))
    
    datatype_container = d.setdefault(data['data_type'], DataType())
    for filename, data in data['files'].iteritems():
        if filename == '.':
            filename = file_root
        file_path = FilePath(filename)
        for tag_set, tags in data.iteritems():
            datatype_container.add_tag_set(tag_set).add_tags(tags, file_path)

if __name__ == '__main__':
    options, args = parser.parse_args()
    logging.basicConfig(level=options.logging_level)
    
    stagfile_re = re.compile('.*\.stag$')
    def find_stagfiles(arg, dirname, names):
        func = curry(os.path.join, dirname)
        arg.extend( map(func, filter(stagfile_re.findall, names)))

    stagfiles = []
    for path in args:
        os.path.walk(os.path.abspath(path), find_stagfiles, stagfiles)

    data = {}
    parse_func = curry(parse_stagfile, data)
    map(parse_func, stagfiles)
    
    print data
