import stat
import errno

import unittest
import fuse
import stag.fs

class TestStagFuse(unittest.TestCase):
    def setUp(self):
        self.fs = stag.fs.StagFuse()

    def test_getattr(self):
        resp = self.fs.getattr('/')

        self.assertTrue(isinstance(resp, fuse.Stat))
        self.assertTrue(resp.st_mode & stat.S_IFDIR)
       
        resp = self.fs.getattr('/this_doesnt_exist')
        self.assertEqual(resp, -errno.ENOENT)
    
    def test_readdir(self):
        for path in ['/']:
            resp = self.fs.readdir(path, 0)
            for i, row in enumerate(resp):
                # First two rows should be . and ..
                if i == 0:
                    self.assertEqual(row.name, '.')
                if i == 1:
                    self.assertTrue(row.name, '..')

                self.assertTrue(isinstance(row, fuse.Direntry))
                self.assertTrue(isinstance(row.name, str)) # Directories must be non-unicode

