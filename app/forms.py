from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, FormField, FieldList
from wtforms.validators import DataRequired


class LoginForm(Form):
	username = StringField('Email', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember_me = BooleanField('remember_me', default=False)


class PasswordChange(Form):
	password = PasswordField('Password', validators=[DataRequired()])


class AddName(Form):
	name = StringField('Name', validators=[DataRequired()])


class KeyValueAdd(Form):
	key = StringField('Attribute Name', validators=[DataRequired()])
	value = StringField('Value', validators=[DataRequired()])

class KeyValueModify(Form):
	mod_key = StringField('Attribute Name', validators=[DataRequired()])
	mod_value = StringField('Value', validators=[DataRequired()])
	mod_delete = BooleanField('delete', default=False)


class MultiKeyValueAdd(Form):
	mkey = StringField('Attribute Name', validators=[DataRequired()])
	mvalue = StringField('Value', validators=[DataRequired()])


class MultiKeyValueModify(Form):
	mod_mkey = StringField('Attribute Name', validators=[DataRequired()])
	mod_mvalue = StringField('Value', validators=[DataRequired()])
	mod_mdelete = BooleanField('delete', default=False)