"""Module for reading and handling result files
"""
import datetime
import re
import requests
from collections import Counter
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
    timestamp = datetime.timedelta(seconds = 0)
    for _, field in self.get_timefields(string):
      group = field.groups()
      times = {
          "minutes": int(group[0] or 0),
          "seconds": int(group[1]) + float(group[2] or 0)}
      newtime = datetime.timedelta(**times)
      if newtime > timestamp:
        timestamp = newtime
    return timestamp

  def get_timefields(self, string):
    """Returns a tuple (index, field) of any time fields
    in the string.  field is a regex match object
    """
    for j, field in enumerate(string.split()):
      match = self.time_pattern.search(field)
      if match:
        yield (j, match)

  def split_on_times(self, string):
    """Splits a string on time fields.  Returns a list of strings
    """
    return re.split("|".join([field[1].string for
      field in self.get_timefields(string)]), string)

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
  def __init__(self,
      date,
      buff = None,
      url = "http://www.coolrunning.com/results/12/ma/Nov3_ECACDi_set1.shtml"):

    self.num_parser = NumParser()
    self.date = date
    if buff:
      self.raw_data = buff.read()
    elif url:
      data = requests.get(url).text
      soup = BeautifulSoup(data)
      if soup.find("pre"):
        self.raw_data = soup.find("pre").get_text()
        self.data_lines = self.raw_data.split("\n")
      else:
        self.raw_data = soup.prettify()
        self.data_lines = re.split(ur"(?:<[Bb][Rr]\s*?/?>)", self.raw_data)
        self.data_lines = [re.sub(ur"[\r\n]+", " ", line) for
            line in self.data_lines]

    self.clean()
    self.hier_lines = [self.hier_parse(line) for line in self.data_lines]
    self.frequencies = self.get_frequencies()
    self.class_words = self.get_class_words()
    self.class_index = self.get_class_index()
    self.results = [Result(line) for line in self.data_lines]
    self.set_results()

  def set_results(self):
    """Sets properties of the result objects
    """
    for result in self.results:
      result_line = result.data['raw_data']
      result.set_time(self.num_parser.return_time(result_line))
      result.set_class(self.get_class(result_line))

  def write(self, path):
    """Writes data back out
    """
    with open(path, 'wb') as buff:
      buff.write("\n".join(self.data_lines))

  def clean(self):
    """Removes empty lines, and any headers/footers
    """
    self.data_lines = [line.lower() for
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
  
  def hier_parse(self, line):
    """Performs some heirarchical clustering on the strings in 
    the results, first splitting by time fields (and removing them),
    then splitting by 2+ whitespaces, then by single white spaces.
    """
    splt = [field for field in self.num_parser.split_on_times(line) if
        len(field.strip()) > 0]
    splt = [re.split(r"\s{2,}", field.strip()) for
        field in splt if len(field) > 0]
    return[[j.split() for j in field] for field in splt if len(field) > 0]

  def get_frequencies(self):
    """Returns frequency counts of all words in the results
    """
    count = Counter()
    for field in "\n".join(self.data_lines).split():
      count[field] += 1
    return count

  def get_class_words(self):
    """ Checks for class year existence
    """
    this_year = self.date.year
    class_words = {str(j):j for j in range(this_year+1, this_year+5)}
    class_words.update({
      "fr": this_year + 4,
      "so": this_year + 3,
      "jr": this_year + 2,
      "sr": this_year + 1})
    counts = self.frequencies
    class_words = {key:value for key, value in class_words.iteritems() if
        0.1 < counts[key]/float(len(self.data_lines)) < 0.5}
    return class_words

  def get_class_index(self):
    """ Returns the index of a class year (assuming it is the same for
    each column
    """
    class_words = self.get_class_words()
    counts = Counter()
    for line in self.data_lines:
      for word in class_words:
        try:
          counts[line.index(word)] += 1
        except ValueError:
          pass
    most_common = counts.most_common()[0]
    if most_common[1]/float(sum(counts.values())) > 0.5:
      return most_common[0]
    return None
  
  def get_class(self, line):
    """ Sets the class year of a result
    """
    if self.class_index:
      for class_word, class_year in self.class_words.iteritems():
        if class_word in line and line.index(class_word) == self.class_index:
          return class_year
    return None



    

class Result:
  """ Handles individual runners in a result
  """
  def __init__(self, data):
    self.data = {
        "raw_data": data,
        "time": None,
        "class": None,
        "school": None,
        "firstname": None,
        "lastname": None,
        "meetname": None,}

  def set_time(self, time):
    """ Set finishing time
    """
    self.data['time'] = time

  def set_school(self, school):
    """ Set school
    """
    self.data['school'] = school

  def set_name(self, firstname, lastname):
    """ Set name
    """
    self.data['firstname'] = firstname
    self.data['lastname'] = lastname

  def set_class(self, classyear):
    """ Set class
    """
    self.data['class'] = classyear

  def set_meet(self, meet):
    """ Set meet
    """
    self.data['meetname'] = meet

  def __str__(self):
    string = "Result:"
    for key, value in self.data.iteritems():
      if value:
        string += "\n\t%s: %s" % (key, value)
    return string

class Course:
  """Handles course data in the result
  """
  def __init__(self,
      name,
      distance):
    self.name = name
    self.distance = int(distance)

def startup():
  """Convenience function to have some initial data
  """
  return Parser(
      date = datetime.date(2012, 11, 3),
      url = 'http://www.coolrunning.com/results/12/ma/Nov3_ECACDi_set1.shtml')

if __name__ == "__main__":
  parser = startup()
  print "\n".join(parser.data_lines)

