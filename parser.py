"""Module for reading and handling result files
"""
import datetime
import re
import requests
from bs4 import BeautifulSoup

ALLOWED_EXTENSIONS = set(["txt"])

def allowed_file(filename):
  """Makes sure file is in the allowed list
  """
  return (("." in filename) and
      (filename.rsplit(".",1)[1] in ALLOWED_EXTENSIONS))


class NumParser:
  """Helper class to parse time and place fields
  """
  def __init__(self):
    self.time_pattern = re.compile(
        r"([0-9]{1,2})?(?::)([0-9]{1,2})(.[0-9]{1,2})?")
    self.place_pattern = re.compile(
        r"^(\d+)(?:\.)?(?<=$)")

  def has_time(self, string):
    """Checks whether the given string has a timestamp in it
    """
    return any(self.time_pattern.match(field) for
        field in string.split())

  def return_time(self, string):
    """Returns largest timestamp from the string
    """
    times = {}
    timestamp = datetime.timedelta(seconds = 0)
    for field in string.split():
      field = self.time_pattern.search(field)
      if field:
        group = field.groups()
        times["minutes"] = int(group[0] or 0)
        times["seconds"] = int(group[1]) + float(group[2] or 0)
        newtime = datetime.timedelta(**times)
        if newtime > timestamp:
          timestamp = newtime
    return timestamp

  def has_place(self, string):
    """Checks whether the given string has a (possible)
    place at the start
    """
    return any(self.place_pattern.match(field) for
        field in string.split())

  def return_place(self, string):
    """Returns a digit at the start of a line
    """
    for field in string.split():
      field = self.place_pattern.match(field)
      if field:
        return int(field.group(1))

class Parser:
  """Handles file parsing operations
  """
  def __init__(self, buff = None, url = None):
    self.num_parser = NumParser()
    if buff:
      self.raw_data = buff.read()
    elif url:
      data = requests.get(url).text
      soup = BeautifulSoup(data)
      if soup.find("pre"):
        self.raw_data = soup.find("pre").get_text()
        self.data_lines = self.raw_data.split("\n")
      else:
        self.data_lines = re.split(ur"(?:<[Bb][Rr]\s*?/?>)", soup.prettify())
        self.data_lines = [re.sub(ur"[\r\n]+", " ", line) for
            line in self.data_lines]

    self.clean()

  def write(self, path):
    """Writes data back out
    """
    with open(path, 'wb') as buff:
      buff.write("\n".join(self.data_lines))

  def clean(self):
    """Removes empty lines, and any headers/footers
    """
    self.data_lines = [line for
        line in self.data_lines if
        self.num_parser.has_time(line) and
        self.num_parser.has_place(line) and
        any(c.isalpha() for c in line)]
    counter = 1
    beginning_found = False
    for j, line in enumerate(self.data_lines):
      if counter == self.num_parser.return_place(line):
        counter += 1
        if counter > 14:
          if not beginning_found:
            beginning_found = True
            good_lines = self.data_lines[j-13:j]
          good_lines.append(line)
      elif not beginning_found:
        counter = 1
    self.data_lines = good_lines

if __name__ == "__main__":
  parser = Parser(url = 'http://plattsys.com/m1shell.asp?eventid=1098')
  print "\n".join(parser.data_lines)

