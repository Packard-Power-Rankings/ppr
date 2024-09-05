import unittest

# commit test on main


def add(x, y):
    return x + y


class TestFunctions(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(3, 3), 6)


if __name__ == '__main__':
    unittest.main()
