""" Controller for APP
"""
import os
import json
import logging
from flask import Flask, render_template, send_from_directory
from flask import request, redirect, url_for
from werkzeug import secure_filename

import mongo_utilities
import forms
from parser import allowed_file, Parser


#----------------------------------------
# initialization
#----------------------------------------

APP = Flask(__name__)
APP.logger.setLevel(logging.INFO)
# Keep passwords and credentials in a .creds file
if os.path.exists(".creds"):
  CREDS = json.load(open(".creds"))

  APP.config.update(
      DEBUG = True,
  )

APP.config["UPLOAD_FOLDER"] = os.path.join(APP.root_path, "raw_data")
APP.logger.info(APP.config["UPLOAD_FOLDER"])
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
  form = forms.UploadForm(request.form)
  APP.logger.info(form.data)
  APP.logger.info(request.files)
  if request.method == "POST" and form.validate():
    results = request.files['file_data']
    if results and allowed_file(results.filename):
      filename = secure_filename(results.filename)
      parser = Parser(
          meetname = form.meetname.data,
          date = form.date.data,
          buff = results)
    elif 'url' in form:
      filename = "test.txt"
      parser = Parser(
          meetname = form.meetname.data,
          date = form.date.data,
          url = form.url.data)
    parser.write(os.path.join(APP.config['UPLOAD_FOLDER'], filename))
    return redirect(url_for('uploaded_results', filename = filename))
  return render_template("upload.html", form=form)

@APP.route("/teams")
def teams():
  """Team index page
  """
  return render_template('teams.html', teams = mongo_utilities.get_teams())

@APP.route("/teams/new", methods = ["GET", "POST"])
def add_team():
  """ Add a new team
  """
  team_name = request.form['team_name']

  APP.logger.info("There was a post!")
  APP.logger.info(request.form)
  if request.method == "POST":
    mongo_utilities.create_team(team_name)
  else:
    return render_template('teams.html', teams = mongo_utilities.get_teams())

@APP.route("/meets")
def meets():
  """Meet index page
  """
  return render_template('meets.html', meets = mongo_utilities.get_meets())

@APP.route("/meets/<meet_id>")
def results(meet_id):
  """Print meet results
  """
  return render_template('results.html',
      results = mongo_utilities.get_meet_results(meet_id))

@APP.route("/courses")
def courses():
  """Course index page
  """
  return render_template('courses.html',
      courses = mongo_utilities.get_courses())

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
