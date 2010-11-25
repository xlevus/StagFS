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
