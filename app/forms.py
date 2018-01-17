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
	key = StringField('Attribute Name', validators=[DataRequired()])
	value = StringField('Value', validators=[DataRequired()])
	delete = BooleanField('delete', default=False)