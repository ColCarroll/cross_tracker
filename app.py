""" Controller for APP
"""
import os
import json
from flask import Flask, render_template, send_from_directory
from flask import request, redirect, url_for
from werkzeug import secure_filename

import parser

#----------------------------------------
# initialization
#----------------------------------------

APP = Flask(__name__)
# Keep passwords and credentials in a .creds file
try:
  CREDS = json.load(open(".creds"))

  APP.config.update(
      DEBUG = True,
  )

  APP.config["SECRET_KEY"] = "\xc62{{x.\xf6\xe1_K\xf3\x85)~\xb3E\xce)\x89j\x823|'"
  APP.config["UPLOAD_FOLDER"] = os.path.join(APP.root_path, "raw_data")
except NameError:
  pass

#----------------------------------------
# database
#----------------------------------------

from mongoengine import connect
from flask.ext.mongoengine import MongoEngine

try:
  APP.config["MONGODB_DB"] = CREDS['DB_NAME']
  connect(CREDS['DB_NAME'],
      host='mongodb://' +
      CREDS['DB_USERNAME'] +
      ':' +
      CREDS['DB_PASSWORD'] +
      '@' +
      CREDS['DB_HOST_ADDRESS'])
  DB = MongoEngine(APP)
except NameError:
  pass

#----------------------------------------
# controllers
#----------------------------------------

@APP.route('/favicon.ico')
def favicon():
  """Route favicon to all pages
  """
  return send_from_directory(
      os.path.join(APP.root_path, 'static'), 'ico/favicon.ico')

@APP.route("/raw_results/<filename>")
def uploaded_results(filename):
  """Serves up raw result files
  """
  return send_from_directory(APP.config["UPLOAD_FOLDER"], filename)

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

@APP.route("/upload", methods = ["GET", "POST"])
def uploads():
  """ Handles file uploads
  """
  if request.method == "POST":
    results = request.files['results']
    if results and parser.allowed_file(results.filename):
      filename = secure_filename(results.filename)
      results.save(os.path.join(APP.config['UPLOAD_FOLDER'], filename))
      print request.form
      return redirect(url_for('uploaded_results', filename = filename))
  return render_template("upload.html")

@APP.route("/meets")
def meets():
  """Front page for app
  """
  return render_template('index.html')

@APP.route("/teams")
def teams():
  """Front page for app
  """
  return render_template('index.html')

@APP.route("/courses")
def courses():
  """Front page for app
  """
  return render_template('index.html')

@APP.route("/predictions")
def predictions():
  """Front page for app
  """
  return render_template('index.html')

#----------------------------------------
# launch
#----------------------------------------

if __name__ == "__main__":
  PORT = int(os.environ.get("PORT", 5000))
  APP.run(host='0.0.0.0', port=PORT)
