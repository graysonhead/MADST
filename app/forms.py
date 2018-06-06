from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, FormField, FieldList, SelectField
from wtforms.validators import DataRequired


class LoginForm(Form):
	username = StringField('Email', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember_me = BooleanField('remember_me', default=False)


class PasswordChange(Form):
	password = PasswordField('Password', validators=[DataRequired()])
	password_confirm = PasswordField('Confirm Password', validators=[DataRequired()])

class AddName(Form):
	name = StringField('Name', validators=[DataRequired()])

class AddAdminUser(Form):
	adminname = StringField('Username', validators=[DataRequired()])

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


class UserCreationForm(Form):
	username = StringField('Username', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	first_name = StringField('First Name', validators=[DataRequired()])
	last_name = StringField('Last Name', validators=[DataRequired()])

class OUName(Form):
	ouname = StringField('Username', validators=[DataRequired()])

# ('Option1', 'Option1'),('Option2', 'Option2')

class AddRole(Form):
	rolename = SelectField('Role Name', coerce=int, validators=[DataRequired()])

class NewRole(Form):
	newrole = StringField('Role Name', validators=[DataRequired()])
	ldap_dn = StringField('LDAP Group DN', validators=[DataRequired()])

class BillingGroup(Form):
	group = StringField('Billing Group', validators=[DataRequired()])

