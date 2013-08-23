"""Utilities for reading/writing
to the mongodb
"""
import datetime
from pymongo import MongoClient

DATE_FMT = "%Y-%m-%d"

CLIENT = MongoClient()
DBNAME = "cross_tracker"
DB = CLIENT[DBNAME]

TEAM_COLLECTION = "teams"
MEET_COLLECTION = "meets"
COURSE_COLLECTION = "courses"
RESULT_COLLECTION = "results"

def time_to_string(*results):
  """Checks for a time field and changes it to 
  a string
  """
  for result in results:
    if 'time' in result:
      result['time'] = str(result['time'])

def string_to_time(*results):
  """Checks for a time field and changes it to 
  a time object
  """
  for result in results:
    if "time" in result:
      time = result["time"].split(":")
      result["time"] = datetime.timedelta(
          hours = int(time[0]),
          minutes = int(time[1]),
          seconds = float(time[2]))

def date_to_string(*results):
  """Checks for a date field and changes it to 
  a string
  """
  for result in results:
    if 'date' in result:
      result['date'] = result['date'].strftime(DATE_FMT)

def string_to_date(*results):
  """Checks for a date field and changes it to 
  a date object
  """
  for result in results:
    if "date" in result:
      result['date'] = datetime.datetime.strptime(result['date'],
          DATE_FMT).date()

# Result utilities

def add_result(**kwargs):
  """Creates a new team
  """
  if 'team' in kwargs:
    create_team(kwargs['team'])
  date_to_string(kwargs)
  time_to_string(kwargs)
  return DB[RESULT_COLLECTION].insert(kwargs)

def get_results(**kwargs):
  """Returns a list of all results
  """
  if kwargs:
    results = DB[RESULT_COLLECTION].find(kwargs)
  else:
    results = DB[RESULT_COLLECTION].find()
  results = [r for r in results]
  string_to_date(*results)
  string_to_time(*results)
  return results

def get_meet_results(meet_id):
  """Return results for a particular meet
  """
  results = DB[RESULT_COLLECTION].find({'meetid': meet_id})
  results = [r for r in results]
  string_to_date(*results)
  return results

# Team utilities

def create_team(team_name, **kwargs):
  """Creates a new team
  """
  kwargs["name"] = team_name
  exists = get_team(team_name)
  if exists:
    return exists['_id']
  kwargs["alias"] = [team_name.lower()]
  return DB[TEAM_COLLECTION].insert(kwargs)

def get_team(team_name):
  """Gets team if it exists
  """
  teams = get_teams()
  for team in teams:
    if team_name.lower() in team["alias"]:
      return team
  return {}

def get_teams():
  """Returns a list of all teams
  """
  return DB[TEAM_COLLECTION].find()


# Meet utilities

def create_meet(meet_name, **kwargs):
  """Creates a new meet
  """
  kwargs["name"] = meet_name

  date_to_string(kwargs)
  return DB[MEET_COLLECTION].insert(kwargs)

def get_meets():
  """Returns a list of all meets
  """
  meets =  [m for m in DB[MEET_COLLECTION].find()]
  string_to_date(*meets)
  return meets

# Meet utilities

def create_course(course_name, **kwargs):
  """Creates a new course
  """
  kwargs["name"] = course_name
  return DB[COURSE_COLLECTION].insert(kwargs)

def get_courses():
  """Returns a list of all courses
  """
  return DB[COURSE_COLLECTION].find()

