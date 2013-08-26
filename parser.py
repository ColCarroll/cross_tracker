"""Module for reading and handling result files
"""
import datetime
import re
import requests
from collections import Counter
from bs4 import BeautifulSoup
import mongo_utilities

ALLOWED_EXTENSIONS = set(["txt"])
def allowed_file(filename):
  """Makes sure file is in the allowed list
  """
  return (("." in filename) and
      (filename.rsplit(".",1)[1] in ALLOWED_EXTENSIONS))

def find_all(regex, string):
  """Returns index of all substrings matching the
  given regex
  """
  return [m.start() for m in re.finditer(regex, string)]

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
      meetname,
      date,
      buff = None,
      url = "http://www.coolrunning.com/results/12/ma/Nov3_ECACDi_set1.shtml"):

    self.num_parser = NumParser()
    self.date = date
    if buff:
      self.raw_data = buff.read()
      self.data_lines = self.raw_data.split("\n")
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
    self.frequencies = self.get_frequencies()
    self.class_words = self.get_class_words()
    self.class_index = self.get_class_index()
    self.hier_lines = [self.hier_parse(line) for line in self.data_lines]
    self.meet_id = mongo_utilities.create_meet(meetname, date = date)
    self.results = [Result(line, self.meet_id, date) for line in self.data_lines]
    self.set_results()
    self.save()

  def get_id(self):
    """Returns meet_id
    """
    return self.meet_id

  def set_results(self):
    """Sets properties of the result objects
    """
    for result in self.results:
      result_line = result.data['raw_data']
      result.set_time(self.num_parser.return_time(result_line))
      textfields = self.find_name(result_line)
      result.set_runner(
          textfields["firstname"],
          textfields["lastname"],
          textfields["team"],
          self.get_class(result_line)['class_year'])
      result.set_team(textfields["team"])

  def write(self, path):
    """Writes data back out
    """
    with open(path, 'wb') as buff:
      buff.write("\n".join(str(result) for result in self.results))

  def save(self):
    """Saves data to mongo database
    """
    for result in self.results:
      mongo_utilities.add_result(**result.data)

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
    the results, first splitting by class field (if existe) and
    time fields, then splitting by 2+ whitespaces, then by
    single white spaces.
    """
    splitfields = [field[1].string for
        field in self.num_parser.get_timefields(line)]
    splt = self.class_split(line)
    splt = reduce(lambda x, y:x+y, [re.split("|".join([field for field in
      splitfields if field]), line)
        for line in splt])
    splt = [re.split(r"\s{2,}", field.strip()) for
        field in splt if len(field) > 0]
    splt = [j.split() for field in splt for j in field if len(field) > 0]
    strings = [[word for word in field if
      re.match("[a-z',-. ()-]+$",word)] for field in splt]
    return [string for string in strings if len(string)>0]

  def find_name(self, line):
    """Returns a firstname, lastname, team tuple for a line
    """
    name_index = self.find_name_index()
    hier = self.hier_parse(line)
    if "," in [j for j in hier[name_index]]:
      name = " ".join(hier[name_index]).split(",")
      return {"firstname": name[1].strip(),
          "lastname": name[0].strip(), 
          "team": " ".join(hier[1])}
    return {"firstname": hier[name_index][0],
        "lastname": " ".join(hier[name_index][1:]),
        "team": " ".join(hier[1])}

  def find_name_index(self):
    """Looks for a person's name by looking for the
    hierarchical field that is usually length 2
    """
    fieldscores = {0:Counter(), 1:Counter()}
    for field in self.hier_lines:
      for j, strlist in enumerate(field):
        fieldscores[j][len(strlist)] += 1
    name_perc = 0
    name_index = 0
    for j in fieldscores:
      new_perc = fieldscores[j][2]/float(sum(fieldscores[j].values()))
      if new_perc > name_perc:
        name_perc = new_perc
        name_index = j
    return name_index

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
    most_common = counts.most_common()
    if most_common and most_common[0][1]/float(sum(counts.values())) > 0.5:
      return most_common[0]
    return None

  def get_class(self, line):
    """ Sets the class year of a result
    """
    if self.class_index:
      for class_word, class_year in self.class_words.iteritems():
        if self.class_index[0] in find_all(class_word, line):
          return {
              'word': class_word,
              'class_year': class_year,
              'index': self.class_index[0]}
    return {'word': None, 'class_year': None, 'index': None}

  def class_split(self, line):
    """ Splits a line by the class year, if exists.  Returns
    a list
    """
    class_info = self.get_class(line)
    if class_info['word']:
      return [line[:class_info['index']],
          line[class_info['index']+len(class_info['word']):]]
    return [line]

class Result:
  """ Handles individual runners in a result
  """
  def __init__(self, data, meet_id, date):
    self.data = {
        "raw_data": data,
        "time": None,
        "team_id": None,
        "runner_id": None,
        "meet_id": meet_id,
        "date": date,}

  def set_time(self, time):
    """ Set finishing time
    """
    self.data['time'] = time

  def set_team(self, team):
    """ Set team
    """
    self.data['team_id'] = mongo_utilities.create_team(team)

  def set_runner(self, firstname, lastname, team, class_year = None):
    """ Set name
    """
    self.data['runner_id'] = mongo_utilities.create_runner(
        firstname,
        lastname,
        team,
        class_year)

  def set_meet(self, meet_id):
    """ Set meet
    """
    self.data['meet_id'] = meet_id

  def __repr__(self):
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
      meetname = "ECAC Championship",
      date = datetime.date(2012, 11, 3),
      buff = open("/Users/colinc/Documents/XCdata/results/ecac2012.txt"))

if __name__ == "__main__":
  parser = startup()
  print "\n".join(parser.data_lines)

