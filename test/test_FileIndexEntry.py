import unittest
from file_index import FileIndexEntry

class TestFileIndexEntry(unittest.TestCase):

    def test_simple_user_input(self):
        entry = FileIndexEntry("testfile", "r")

        inp = entry.generate_user_input()

        id, action, filename = inp.split()
        self.assertEqual(id, entry.get_uid())
        self.assertEqual(action, "r")
        self.assertEqual(filename, "testfile")

    def test_complex_user_input(self):
        entry = FileIndexEntry("testfile1", "c")
        entry.add_target_name("testfile2", "l")

        inp = entry.generate_user_input()
        inp = inp.strip() # drop the newline
        rows = inp.split("\n")
        self.assertEqual(len(rows), 2, "Input is:\n%s" % inp)

        id, action, filename = rows[0].split()
        self.assertEqual(id, entry.get_uid())
        self.assertEqual(action, "c")
        self.assertEqual(filename, "testfile1")

        id, action, filename = rows[1].split()
        self.assertEqual(id, entry.get_uid())
        self.assertEqual(action, "l")
        self.assertEqual(filename, "testfile2")


if __name__ == "__main__":
    unittest.main()
