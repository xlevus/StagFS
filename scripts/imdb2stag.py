#!/usr/bin/env python

#    Copyright (C) 2009  Chris Targett  <chris@xlevus.net>
#    Contributions by: Lachlan Stuart.
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

"""
A small script to generate a StagFS .stag files for movies.

It expects the movie to be in a well-formatted folder and not an individual file. e.g.

    + 2001 A Space Odyssey (1968)
        movie.stag
        2001.A.Space.Odyssey.avi
        2001.A.Space.Odyssey.sub

    + Blade Runner (1982)
        movie.stag
        bladerunner.avi

"""
import re
import sys
import imdb
import urllib
import urllib2

if imdb.__version__ <= "4.1":
    print "imdb2stag requires a version of IMDbPY greater than 4.1"
    exit(1)

import os.path
import logging
import simplejson as json
from optparse import OptionParser

# The data type of the .stag file. This will also be used as the filename
DATA_TYPE = "movie"

parser = OptionParser(usage="%prog [options] folder1 folder2 ...", version='0.1')
parser.add_option("--data-file", dest="data_file", 
        default="%s.stag"%DATA_TYPE, help="File to write data to")
parser.add_option("--debug", '-d', dest="logging_level", action="store_const", 
        const=logging.DEBUG, help="Display debug messages", default=logging.INFO)
parser.add_option("--quiet", dest="logging_level", action="store_const", 
        const=logging.CRITICAL, help="Display only critical errors")
parser.add_option("--skip-write", dest="write_file", action="store_false", 
        default=True, help="Don't actually write the tags file")
parser.add_option("--overwrite", '-F', dest="overwrite_existing", action="store_true", 
        default=False, help="Force overwrite of existing tag files")
parser.add_option("--interactive", dest="interactive", action="store_true", 
        default=False, help="Prompt for a selection on multiple results")
parser.add_option('--jfgi', dest='google', action='store_true', default=False,
        help="Google the title instead of use IMDb")

ia = imdb.IMDb()

class NoMovieFound(Exception):
    pass

def get_input(movie_count):
    """Wrapper around raw_input to validate the input."""

    rawinput = raw_input("Select an option: ")
    try:
        input = int(rawinput)
        if input <= 0 or input > movie_count:
            raise ValueError
        return input
    except ValueError:
        print "Unable to parse '%s'" % rawinput
        return get_input(movie_count)

def get_title_from_google(movie_name, interactive=False):
    try:
        query = urllib.quote("site:www.imdb.com/title/ " + movie_name)
        url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=' + query
        data_string = urllib2.urlopen(url).read()
        first_result = json.loads(data_string)["responseData"]["results"][0]
        m = re.match("http://www.imdb.com/title/tt(.*)/", first_result["url"])
        imdb_id = m.groups()[0]
    except (AttributeError, IndexError):
        raise NoMovieFound("Unable to find movie for '%s'" % movie_name)

    return ia.get_movie(imdb_id)

def get_title_from_imdb(movie_name, interactive=False):
    """
    Searches for a film on IMDb.
    * If only one result is found return that
    * If no films are found, return an error.
    * If more than one film is found, either return an error
      when not in interactive mode, or prompt for a selection
    """
    s_result = ia.search_movie(movie_name)
    logging.debug("Found %s results for film '%s'" % (len(s_result), movie_name))
    if len(s_result) == 1:
        return get_data_for_movie(s_result[0])
    elif len(s_result) == 0:
        raise NoMovieFound("Unable to find movie for '%s'" % movie_name)
    else:
        if interactive:
            for i,movie in enumerate(s_result):
                print u"\t%s: %s (%s) (%s)" % (i+1, movie, movie.get('year', 'Unknown'), movie.get('kind', 'unknown'))
            result_num = get_input(len(s_result))
            print
            return s_result[result_num]
        else:
            raise NoMovieFound("Found %s results for for '%s'" % (len(s_result), movie_name))

def get_data_for_movie(movie):
    """
    Takes an IMDbPY movie object, updates it and
    formats it into a stagfs friendly dict.
    """

    # Not all data was retrieved so update the movie object
    ia.update(movie)
    ia.update(movie, 'keywords')

    output = {
        'title': movie.get('title', []),
        'canonical_title': movie.get('canonical title', []),
        'year': movie.get('year', []),
        'genre': movie.get('genres', []),
        'director': [x['name'] for x in movie.get('director', [])],
        'writer': [x['name'] for x in movie.get('writer',[])],
        'cast': [x['name'] for x in movie.get('cast',[]) ],
        'keywords': [x.replace(u'\xa0',' ') for x in movie.get('keywords',[])],
        'languages': movie.get('languages', []),
        'countries': movie.get('countries', []),
        'imdb_url': 'http://www.imdb.com/title/tt%s/' % movie.getID(),
    }

    from math import floor, ceil

    rating = movie.get('rating')
    output['rating (exact)'] = str(rating)
    output['rating (range)'] = '%g.0-%g.9' % (floor(rating), floor(rating))

    return output

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
                # Already tagged, skip it.
                logging.debug("Tag file '%s' already exists" % data_file)
                continue

        # Extract the folder name from the path and attempt to find it on IMDb
        try:
            movie_name = os.path.basename(folder)
            if options.google:
                movie_obj = get_title_from_google(movie_name, False)
            else:
                movie_obj = get_title_from_imdb(movie_name, options.interactive)
            folder_data = get_data_for_movie(movie_obj)
        except (NoMovieFound, urllib2.URLError), e:
            logging.error(e)
            continue
        
        data = {
            'data_type': DATA_TYPE,
            'files': {
                '.': folder_data,
            }
        }

        if options.write_file:
            if folder_data.has_key('error'):
                logging.info("Found an error in '%s'" % data_file)

            try:
                f = open(data_file, 'w')
                json.dump(data, f, indent=4, sort_keys=True)
                logging.debug("Wrote tag file '%s'" % data_file)
            except IOError, e:
                logging.error("Error writing to '%s': %s" % (e.filename, e.strerror))

        logging.info("Processed '%s'" % folder )

    print
