"""Unit tests
"""
import app
import unittest

class CrossUploadPage(unittest.TestCase):
  """Tests the upload page functionality
  """
  def setUp(self):
    """Set up variables
    """
    app.APP.config["TESTING"] = True
    self.app = app.APP.test_client()

  def tearDown(self):
    """ Tear down variables
    """
    pass

  def test_upload_page(self):
    """Visit upload page
    """
    rv = self.app.get('/')
    print rv.data

if __name__ == '__main__':
  unittest.main()
