#
# test_main.py
#
# Testing the base route functions for the FastAPI application.
#
# Takes in a .csv file and sends it to routers/teams.py
# that parses it to JSON.
#

import unittest


def add(x, y):
    return x + y


class TestFunctions(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(3, 3), 6)


if __name__ == '__main__':
    unittest.main()
