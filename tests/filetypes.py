import os
import stat
import errno
import unittest

from fuse import Stat
from stag.filetypes import *

class StagFileTestCase(unittest.TestCase):
    def setUp(self):
        self.file = StagFile()

    def test_getattr(self):
        result = self.file.getattr()
        self.assertEqual(result.__class__, Stat)

        self.assertEqual(result.st_ino, 0)
        self.assertEqual(result.st_dev, 0)
        self.assertEqual(result.st_nlink, 0)
        self.assertEqual(result.st_uid, os.getuid())
        self.assertEqual(result.st_gid, os.getgid())
        self.assertEqual(result.st_size, 0)

class VirtualDirectoryTestCase(unittest.TestCase):
    def test_readdir(self):
        contents = ['a','b','c']
        vd = VirtualDirectory(contents=contents)
        self.assertEqual(vd.readdir(), contents)

    def test_unicode(self):
        contents = [u'\xe2abc']
        vd = VirtualDirectory(contents=contents)
        self.assertEqual(vd.readdir(), ['?abc'])

    def test_getattr(self):
        vd = VirtualDirectory(contents=['a','b','c'])
        result = vd.getattr()

        self.assertTrue(result.__class__, Stat)
        self.assertEqual(result.st_mode & stat.S_IFDIR, stat.S_IFDIR)

class RealFileTestCase1(unittest.TestCase):
    """RealFile test case for when the target is a file"""
    def setUp(self):
        self.file = __file__
        self.rf = RealFile(self.file)

    def test_getattr(self):
        """
        Check the output of the RealFile's getattr
        matches the values of the file it's pointing to
        """
        file_stat = os.stat(self.file)
        result = self.rf.getattr()
        self.assertTrue(result.__class__, Stat)

        self.assertEqual(result.st_mode, file_stat[0])
        self.assertEqual(result.st_ino, file_stat[1])
        self.assertEqual(result.st_dev, file_stat[2])
        self.assertEqual(result.st_nlink, file_stat[3])
        self.assertEqual(result.st_uid, file_stat[4])
        self.assertEqual(result.st_gid, file_stat[5])
        self.assertEqual(result.st_size, file_stat[6])
        self.assertEqual(result.st_atime, file_stat[7])
        self.assertEqual(result.st_mtime, file_stat[8])
        self.assertEqual(result.st_ctime, file_stat[9])

    def test_readdir(self):
        self.assertEqual(self.rf.readdir(), errno.ENOTDIR)

class RealFileTestCase2(RealFileTestCase1):
    """RealFile test case for when the target is a directory"""
    def setUp(self):
        self.file = os.path.split(__file__)[0]
        self.rf = RealFile(self.file)

    def test_readdir(self):
        result = self.rf.readdir()
        self.assertEqual(result, os.listdir(self.file))

