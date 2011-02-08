import unittest

from stag.filetypes import *

class VirtualDirectoryTestCase(unittest.TestCase):
    def test_readdir(self):
        contents = [1,2,3,4,5]
        vd = VirtualDirectory(contents=contents)
        self.assertEqual(vd.readdir(), contents)
