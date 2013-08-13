""" Controller for APP
"""
import os
import json
from flask import Flask, render_template, send_from_directory

#----------------------------------------
# initialization
#----------------------------------------

APP = Flask(__name__)
# Keep passwords and credentials in a .creds file
CREDS = json.load(open(".creds"))

APP.config.update(
    DEBUG = True,
)

APP.config["SECRET_KEY"] = "\xc62{{x.\xf6\xe1_K\xf3\x85)~\xb3E\xce)\x89j\x823|'"

#----------------------------------------
# database
#----------------------------------------

from mongoengine import connect
from flask.ext.mongoengine import MongoEngine

APP.config["MONGODB_DB"] = CREDS['DB_NAME']
connect(CREDS['DB_NAME'],
    host='mongodb://' +
    CREDS['DB_USERNAME'] +
    ':' +
    CREDS['DB_PASSWORD'] +
    '@' +
    CREDS['DB_HOST_ADDRESS'])
DB = MongoEngine(APP)

#----------------------------------------
# controllers
#----------------------------------------

@APP.route('/favicon.ico')
def favicon():
  """Route favicon to all pages
  """
  return send_from_directory(
      os.path.join(APP.root_path, 'static'), 'ico/favicon.ico')

@APP.errorhandler(404)
def page_not_found(_):
  """404 page
  """
  return render_template('404.html'), 404

@APP.route("/")
def index():
  """Front page for app
  """
  return render_template('index.html')

#----------------------------------------
# launch
#----------------------------------------

if __name__ == "__main__":
  PORT = int(os.environ.get("PORT", 5000))
  APP.run(host='0.0.0.0', port=PORT)
