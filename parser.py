"""Module for reading and handling result files
"""

ALLOWED_EXTENSIONS = set(["txt"])

def allowed_file(filename):
  """Makes sure file is in the allowed list
  """
  return (("." in filename) and
      (filename.rsplit(".",1)[1] in ALLOWED_EXTENSIONS))
