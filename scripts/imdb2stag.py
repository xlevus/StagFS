#!/usr/bin/env python

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

import imdb
import os.path
import logging
import simplejson as json
from optparse import OptionParser

DATA_TYPE = "movie"

parser = OptionParser(usage="%prog [options] folder1 folder2 ...", version='0.1')
parser.add_option("--data-file", dest="data_file", default="%s.stag"%DATA_TYPE, help="File to write data to")
parser.add_option("--debug", dest="logging_level", action="store_const", const=logging.DEBUG, help="Display debug messages", default=logging.INFO)
parser.add_option("--quiet", dest="logging_level", action="store_const", const=logging.CRITICAL, help="Display only critical errors")
parser.add_option("--skip-write", dest="write_file", action="store_false", default=True, help="Don't actually write the tags file")
parser.add_option("--overwrite", dest="overwrite_existing", action="store_true", default=False, help="Force overwrite of existing tag files")
parser.add_option("--interactive", dest="interactive", action="store_true", default=False, help="Prompt for a selection on multiple results")

ia = imdb.IMDb()

def get_input(movie_count):
    rawinput = raw_input("Select an option: ")
    try:
        input = int(rawinput)
        if input <= 0 or input > movie_count:
            raise ValueError
        return input
    except ValueError:
        print "Unable to parse '%s'" % rawinput
        return get_input(movie_count)

def get_data_for_title(movie_name, interactive=False):
    s_result = ia.search_movie(movie_name)
    logging.debug("Found %s results for film '%s'" % (len(s_result), movie_name))
    if len(s_result) == 1:
        return get_data_for_movie(s_result[0])
    elif len(s_result) == 0:
        return {'error':'No movies found'}
    else:
        if interactive:
            for i,movie in enumerate(s_result):
                print u"\t%s: %s (%s) (%s)" % (i+1, movie, movie.get('year', 'Unknown'), movie.get('kind', 'unknown'))
            result_num = get_input(len(s_result))
            print
            return get_data_for_movie(s_result[result_num])
        else:
            return {'error': '%s movies found' % len(s_result)}

def get_data_for_movie(movie):
    ia.update(movie)
    ia.update(movie, 'keywords')

    data = {
        'title': movie.get('title', []),
        'canonical_title': movie.get('canonical title', []),
        'year': movie.get('year', []),
        'genre': movie.get('genres', []),
        'director': [x['name'] for x in movie.get('director', [])],
        'writer': [x['name'] for x in movie.get('writer',[])],
        'cast': [x['name'] for x in movie.get('cast',[]) ],
        'keywords': [x.replace(u'\xa0',' ') for x in movie.get('keywords',[])]
    }
    return data

if __name__ == '__main__':
    options, args = parser.parse_args()
    logging.basicConfig(level=options.logging_level)

    for folder in map(os.path.abspath, args):
        logging.debug("Processing folder '%s'" % folder)

        if not os.path.exists(folder):
            logging.warn("Folder '%s' not found" % folder)
            continue

        data_file = os.path.join(folder, options.data_file)
        if os.path.exists(data_file):
            # TODO: Merge existing tag data in a non-destructive manner
            if options.overwrite_existing:
                logging.warn("Overwriting existing tag file '%s'" % data_file)
            else:
                logging.debug("Tag file '%s' already exists" % data_file)
                exit(0)


        movie_name = os.path.basename(folder)
        folder_data = get_data_for_title(movie_name, options.interactive)
        
        data = {
            'data_type': DATA_TYPE,
            'files': {
                '.': folder_data,
            }
        }

        if options.write_file:
            if folder_data.has_key('error'):
                logging.warn("Found an error in '%s'" % data_file)

            f = open(data_file, 'w')
            json.dump(data, f, indent=4, sort_keys=True)
            logging.debug("Wrote tag file '%s'" % data_file)

        print
