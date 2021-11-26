import unittest
import unittest.mock
import os
from ifstool import do_action_copy_move_common
from configuration import Configuration
from os_abstraction import IOSAbstraction

class TestActions(unittest.TestCase):

    def __init__(self, method_name):
        def mocked_split_path(path):
            return (os.path.dirname(path), os.path.basename(path))

        unittest.TestCase.__init__(self, method_name)
        self.config = Configuration()
        self.config.prompt_on_actions = False
        self.os_mock = IOSAbstraction()
        self.os_mock.split_path = mocked_split_path

    def test_rename(self):
        def mocked_isdir(path):
            return True

        self.os_mock.rename_move = unittest.mock.MagicMock(
                return_value=[True, ""])
        self.os_mock.isdir = mocked_isdir

        result, remarks = do_action_copy_move_common("/dir1/filename.txt", "/dir1/new_filename.txt", "r", self.os_mock, self.config)
        self.os_mock.rename_move.assert_called_with("/dir1/filename.txt", "/dir1/new_filename.txt")

        self.assertTrue(result)
        self.assertEqual(0, len(remarks))

if __name__ == "__main__":
    unittest.main()

