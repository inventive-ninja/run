import unittest
from run.library.find.not_found import NotFound


class NotFoundTest(unittest.TestCase):

    # Public

    def test(self):
        self.assertTrue(issubclass(NotFound, Exception))