"""Classes for forms
"""
from wtforms import Form, TextField, FileField, DateField
from wtforms import validators

class RequiredIfNot(validators.Required):
  """A validator which makes a field required if
  another field is set and has a truthy value
  """
  def __init__(self, other_field_name, *args, **kwargs):
    self.other_field_name = other_field_name
    super(RequiredIfNot, self).__init__(*args, **kwargs)

  def __call__(self, form, field):
    other_field = form._fields.get(self.other_field_name)
    if other_field is None and not field.data:
      raise Exception('Required if "%s" is missing' % self.other_field_name)

class UploadForm(Form):
  """ Upload new results
  """
  date = DateField('Date', format= "%Y-%m-%d", id="dp")
  meetname = TextField('Meet Name')
  course = TextField('Course Name')
  distance = TextField('Course Distance')
  url = TextField('Result URL')
  file_data = FileField('Upload file')
