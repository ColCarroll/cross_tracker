""" Controller for APP
"""
import os
import json
from flask import Flask, render_template, send_from_directory
from flask import request, redirect, url_for
from werkzeug import secure_filename

import forms
from parser import allowed_file, Parser

#----------------------------------------
# initialization
#----------------------------------------

APP = Flask(__name__)
# Keep passwords and credentials in a .creds file
if os.path.exists(".creds"):
  CREDS = json.load(open(".creds"))

  APP.config.update(
      DEBUG = True,
  )

  APP.config["UPLOAD_FOLDER"] = os.path.join(APP.root_path, "raw_data")

#----------------------------------------
# database
#----------------------------------------

from mongoengine import connect
from flask.ext.mongoengine import MongoEngine

if os.path.exists(".creds"):
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
  if request.method == "POST" and form.validate():
    results = request.files['results']
    if results and allowed_file(results.filename):
      filename = secure_filename(results.filename)
      parser = Parser(
          meetname = form.meetname.data,
          date = form.date.data,
          buff = results)
    elif 'url' in request.form:
      filename = "test.txt"
      parser = Parser(
          meetname = form.meetname.data,
          date = form.date.data,
          url = form.url.data)
    parser.write(os.path.join(APP.config['UPLOAD_FOLDER'], filename))
    return redirect(url_for('uploaded_results', filename = filename))
  return render_template("upload.html", form=form)

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
