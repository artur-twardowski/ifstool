import unittest
from ifstool import run

class TestApplication(unittest.TestCase):
    def test_help_screen(self):
        self.assertRaises(SystemExit, run, ["--help"])

    def test_exts_help_screens(self):
        self.assertRaises(SystemExit, run, ["-xdf:help"])
        self.assertRaises(SystemExit, run, ["-xcadf.audio:help"])


