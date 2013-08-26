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
RUNNER_COLLECTION = "runners"

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
  """Creates a new result
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
  results = [r for r in DB[RESULT_COLLECTION].find({'meet_id': meet_id})]
  runners = {r['_id']: r for r in 
      DB[RUNNER_COLLECTION].find(
        {'_id': {'$in':
          [result['runner_id'] for result in results]}})}
  teams = {t['_id']: t for t in 
      DB[TEAM_COLLECTION].find(
        {'_id': {'$in':
          [result['team_id'] for result in results]}})}
  results = [r for r in results]
  for r in results:
    r['team'] = teams[r['team_id']]['name']
    r['runner'] = runners[r['runner_id']]['display_name']
    r['class'] = runners[r['runner_id']]['class_year']
  string_to_date(*results)
  return results

# Runner utilities

def create_runner(first_name, last_name, team, class_year):
  """Creates a new runner
  """
  runner = {
      "first_name" : first_name.title(),
      "last_name" : last_name.title(),
      "display_name" : "%s %s" % (first_name.title(),
        last_name.title()),
      "team_id" : create_team(team),
      "class_year" : class_year
      }
  exists = get_runner(runner)
  if exists:
    return exists['_id']
  return DB[RUNNER_COLLECTION].insert(runner)

def get_runner(kwargs):
  """Gets runner if it exists
  """
  return DB[RUNNER_COLLECTION].find_one(kwargs)

def get_runners():
  """Returns a list of all runners
  """
  return DB[RUNNER_COLLECTION].find()


# Team utilities

def create_team(team_name, **kwargs):
  """Creates a new team
  """
  kwargs["name"] = team_name.title()
  exists = get_team(team_name)
  if exists:
    return exists['_id']
  kwargs["alias"] = [team_name.lower()]
  return DB[TEAM_COLLECTION].insert(kwargs)

def get_team(team_name):
  """Gets team if it exists
  """
  return DB[TEAM_COLLECTION].find_one({"alias": team_name.lower()})

def get_teams():
  """Returns a list of all teams
  """
  return DB[TEAM_COLLECTION].find()

def get_team_info(team_id):
  """Returns all info associated with a team
  """
  team = DB[TEAM_COLLECTION].find_one({"_id": team_id})
  runners = [r for r in DB[RUNNER_COLLECTION].find({"team_id": team_id})]
  return {"team": team,
      "runners": runners}
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

# Course utilities

def create_course(course_name, **kwargs):
  """Creates a new course
  """
  kwargs["name"] = course_name
  return DB[COURSE_COLLECTION].insert(kwargs)

def get_courses():
  """Returns a list of all courses
  """
  return DB[COURSE_COLLECTION].find()

