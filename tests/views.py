import unittest
from mock import Mock, patch

from stag.data import DataManager
from stag.views import ViewManager, View

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
        
        self.assertEqual(list(view_manager.get('/')), list(view_manager.get_root()))
        resp = view_manager.get_root()
        self.assertEqual(list(resp), ['movie'])

    def test_custom_view(self):
        """Check that the view manager delegates sub-paths to defined views."""
        class NewView(View):
            def get(self):
                pass
        view_manager = ViewManager(self.db_name, {'movie':NewView})

        NewView.get = Mock(return_value=[])
        view_manager.get('/movie/test')
        NewView.get.assert_called_with('/test')
    
        NewView.get = Mock(return_value=[]) # Reset NewView.get.called
        view_manager.get('/other/test')
        self.assertFalse(NewView.get.called)

