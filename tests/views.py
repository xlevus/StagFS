import os.path
import unittest
from mock import Mock, patch

from stag import filetypes
from stag.data import DataManager
from stag.db import ConnectionWrapper
from stag.views import Dispatcher, View, DoesNotExist

from stag.fs import TEMP_CONFIG

def path_relative_to_source(path):
    # This might be a bit wonky depends on where you call it from
    return os.path.join(os.path.abspath(TEMP_CONFIG['source_folders'][0]), path)

class DispatcherTest(unittest.TestCase):
    def setUp(self):
        self.db_name = TEMP_CONFIG['db_name']
        data = DataManager(
            db_name = self.db_name,
            source_folders = TEMP_CONFIG['source_folders'],
            loaders = TEMP_CONFIG['loaders'],
        )
        data.load_initial()
        self.dispatcher = Dispatcher(self.db_name)
    
    def test_root(self):
        """
        Check that the root path returns a VirtualDirectory object containing
        all of the datatypes.
        """
        root = self.dispatcher.get('/')
        #self.assertIsInstance(root, filetypes.VirtualDirectory)
        self.assertEqual(root.__class__, filetypes.VirtualDirectory)
        self.assertEqual(root._contents, ['movie'])
    
    def test_get_view(self):
        """
        Check that get_view() returns a View object, and make
        sure that subsequent calls return the same object.
        """
        dt = 'movie'
        result = self.dispatcher.get_view(dt)
        self.assertEqual(result.__class__, View)
        self.assertEqual(result.datatype, dt)
        self.assertEqual(result, self.dispatcher.get_view(dt))

    def test_call_view(self):
        """
        Check that deeper paths calls the view with the right arguments
        """
        movie_view = View('movie')
        other_view = View('other')
        movie_view.get = Mock(return_value=filetypes.VirtualDirectory(contents=[]))
        other_view.get = Mock(return_value=filetypes.VirtualDirectory(contents=[]))
        self.dispatcher.views = {'movie':movie_view, 'other':other_view}

        self.dispatcher.get('/movie')
        movie_view.get.assert_called_with('/', self.db_name)

        self.dispatcher.get('/other/test/path')
        other_view.get.assert_called_with('/test/path', self.db_name)
        
        self.assertRaises(DoesNotExist, 
                lambda: self.dispatcher.get('/nonexistant/view'))


class ViewTest(unittest.TestCase):
    def setUp(self):
        self.db_name = TEMP_CONFIG['db_name']
        data = DataManager(
            db_name = self.db_name,
            source_folders = TEMP_CONFIG['source_folders'],
            loaders = TEMP_CONFIG['loaders'],
        )
        data.load_initial()
        self.view = View(datatype='movie')

    def test_root(self):
        result = self.view.get('/', self.db_name)
        self.assertEqual(result.__class__, filetypes.VirtualDirectory)
        self.assertEqual(result._contents, 
                [u'languages', u'writer', u'countries', u'title', 
                    u'imdb_id', u'director', u'cast', u'rating (exact)', 
                    u'rating (range)', u'keywords', u'year', u'genre', u'canonical_title'])

    def test_valid_path(self):
        result = self.view.get('/languages', self.db_name)
        self.assertEqual(result.__class__, filetypes.VirtualDirectory)
        self.assertEqual(result._contents, [u'English', u'Spanish'])

    def test_valid_path2(self):
        result = self.view.get('/languages/English', self.db_name)
        self.assertEqual(result.__class__, filetypes.VirtualDirectory)
        self.assertEqual(result._contents, [u'Bad Taste (1987)', u'Death Race (2008)', 
            u'The Terminator (1984)', u'Michael Clayton (2007)'])

    def test_realfile(self):
        """Check that a path containing a real file returns a RealFile object"""
        result = self.view.get('/languages/English/Bad Taste (1987)', self.db_name)
        self.assertEqual(result.__class__, filetypes.RealFile)
        self.assertEqual(result._target, path_relative_to_source("Bad Taste (1987)"))

    def test_missing_path(self):
        self.assertRaises(DoesNotExist, 
                lambda: self.view.get('/not/existant/path', self.db_name))

