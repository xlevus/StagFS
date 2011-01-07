import unittest
from mock import Mock, patch

from stag.data import DataManager
from stag.views import ViewManager, View, DoesNotExist

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

    def test_get_datatypes(self):
        """Make sure ViewManager.get_datatypes returns the correct values"""
        view_manager = ViewManager(self.db_name)
        self.assertEqual(['movie'], view_manager.get_datatypes())        

    def test_get_root(self):
        """Check the root path returns a list of datatypes and registered views."""
        view_manager = ViewManager(self.db_name, {'UNUSED':View})
        
        resp = set(view_manager.get_root())
        self.assertEqual(set(view_manager.get('/')), resp)
        self.assertEqual(resp, set(['movie','UNUSED']))

    def test_custom_view(self):
        """Check that the view manager delegates sub-paths to defined views."""
        class NewView(View):
            pass
        view_manager = ViewManager(self.db_name, {'movie':NewView, 'other':View})

        # Check 'movie' view gets called with the right path
        NewView.get = Mock(return_value=[])
        view_manager.get('/movie/test')
        NewView.get.assert_called_with('/test')
    
        # Check that call to another view doesn't get misplaced
        NewView.get = Mock(return_value=[]) # Reset NewView.get.called
        view_manager.get('/other/test')
        self.assertFalse(NewView.get.called)

        # Check that a call to a non-registered view or nonexistant datatype raises
        self.assertRaises(DoesNotExist, lambda: view_manager.get('/nonexistant/test'))
