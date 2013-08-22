"""Utilities for reading/writing
to the mongodb
"""
from pymongo import MongoClient

CLIENT = MongoClient()
DBNAME = "cross_tracker"
DB = CLIENT[DBNAME]

TEAM_COLLECTION = "teams"

def create_team(team_name, **kwargs):
  """Creates a new team
  """
  kwargs["name"] = team_name
  kwargs["alias"] = [team_name.lower()]
  return DB[TEAM_COLLECTION].insert(kwargs)

def get_teams():
  """Returns a list of all teams
  """
  return DB[TEAM_COLLECTION].find()


