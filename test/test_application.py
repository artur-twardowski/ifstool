import unittest
from ifstool import run

class TestApplication(unittest.TestCase):
    def test_help_screen(self):
        self.assertRaises(SystemExit, run, ["--help"])


