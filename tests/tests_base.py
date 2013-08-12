from __future__ import unicode_literals

import os
import gzip
import tempfile
import unittest

from pystorages.base import File
from pystorages.move import file_move_safe
from pystorages.base import ContentFile

TEST_TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp')

class StorageTest(unittest.TestCase):
    pass

class ContentFileTest(unittest.TestCase):
    pass

class FileTests(unittest.TestCase):
    def test_context_manager(self):
        orig_file = tempfile.TemporaryFile()
        base_file = File(orig_file)
        with base_file as f:
            self.assertIs(base_file, f)
            self.assertFalse(f.closed)
        self.assertTrue(f.closed)
        self.assertTrue(orig_file.closed)

    def test_file_mode(self):
        # Should not set mode to None if it is not present.
        # See #14681, stdlib gzip module crashes if mode is set to None
        file = File("mode_test.txt", b"content")
        self.assertFalse(hasattr(file, 'mode'))
        g = gzip.GzipFile(fileobj=file)


class FileMoveSafeTests(unittest.TestCase):
    def test_file_move_overwrite(self):
        handle_a, self.file_a = tempfile.mkstemp(dir=TEST_TEMP_DIR)
        handle_b, self.file_b = tempfile.mkstemp(dir=TEST_TEMP_DIR)

        # file_move_safe should raise an IOError exception if destination file exists and allow_overwrite is False
        self.assertRaises(IOError, lambda: file_move_safe(self.file_a, self.file_b, allow_overwrite=False))

        # should allow it and continue on if allow_overwrite is True
        self.assertIsNone(file_move_safe(self.file_a, self.file_b, allow_overwrite=True))
