import unittest

from stag.data import DataManager
from stag.views import ViewManager

from stag.fs import TEMP_CONFIG

class ViewManagerTest(unittest.TestCase):
    def setUp(self):
        self.db_name = TEMP_CONFIG['db_name']
        data = DataManager(
            db_name = self.db_name,
            source_folders = TEMP_CONFIG['source_folders'],
            loaders = TEMP_CONFIG['loaders'],
        )
        data.load_initial()


    def test_get_root(self):
        """Check the root path returns a list of datatypes"""
        view_manager = ViewManager(self.db_name)
        
        self.assertEqual(view_manager.get('/'), view_manager.get_root())
        resp = view_manager.get_root()
        self.assertEqual(resp, ['movie'])

    def test_custom_view(self):
        view_manager = ViewManager(self.db_name, {'movie': None})
