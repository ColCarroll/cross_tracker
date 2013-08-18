"""Functional tests for cross country app
"""

from selenium import webdriver
import unittest

class NewVisitorTest(unittest.TestCase):
  """ Test new visitor flow
  """
  def setUp(self):
    self.browser = webdriver.Firefox()
    self.browser.implicitly_wait(3)

  def tearDown(self):
    self.browser.quit()

  def test_can_start_and_upload_a_file(self):
    #We visit the cross country prediction page
    self.browser.get('http://localhost:5000')
    self.assertIn("Cross Country", self.browser.title)

if __name__ == '__main__':
  unittest.main()
