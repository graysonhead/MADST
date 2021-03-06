from app import db, config, crypt
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import os
from binascii import hexlify
import datetime
from hashlib import md5

def _get_date():
	return datetime.datetime.now()

# task_table = db.Table('task_table',
# 					  db.Column(
# 						  'organization_id', db.Integer, db.ForeignKey('organization.id')
# 					  ),
# 					  db.Column(
# 						  'task_id', db.Integer, db.ForeignKey('task.id')
# 					  )
# 					  )


role_table = db.Table('user_role',
					  db.Column(
						  'user_id', db.Integer, db.ForeignKey('user.id')
					  ),
					  db.Column(
						  'role_id', db.Integer, db.ForeignKey('role.id')
					  )
)

admin_user_table = db.Table('admin_user_table',
							db.Column(
								'user_id', db.Integer, db.ForeignKey('user.id')
							),
							db.Column(
								'organization_id', db.Integer, db.ForeignKey('organization.id')
							)
)

status_map = db.Table('status_map',
					  db.Column(
						  'status_id', db.Integer, db.ForeignKey('status.id')
					  ),
					  db.Column(
						  'task_id', db.Integer, db.ForeignKey('task.id')
					  )
)

role_template_map = db.Table('role_template_map',
					 db.Column(
						'role_id', db.Integer, db.ForeignKey('role.id')
					 ),
					 db.Column(
						 'usertemplate_id', db.Integer, db.ForeignKey('user_template.id')
					 )
)



class Role(db.Model):
	__tablename__ = 'role'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(120), unique=True)
	disabled = db.Column(db.Boolean())
	ldap_group_dn = db.Column(db.String(120))
	users = relationship(
		"User",
		secondary=role_table,
		back_populates="roles"
	)
	usertemplates = relationship(
		"UserTemplate",
		secondary=role_template_map,
		back_populates="roles"
	)

	def __init__(self, name):
		self.name = name.lower()

	def __repr__(self):
		return '<Role {}>'.format(self.name)

	def __str__(self):
		return self.name


class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	first_name = db.Column(db.String(120))
	last_name = db.Column(db.String(120))
	username = db.Column(db.String(120), unique=True)
	email = db.Column(db.String(120), unique=True)
	password = db.Column(db.String(120))
	sync_password = db.Column(db.String(120))
	sync_username = db.Column(db.String(120))
	disabled = db.Column(db.String(120))
	is_ldap_user = db.Column(db.String(120))
	ldap_guid = db.Column(db.String(120))
	__tablename__ = 'user'
	tasks = relationship("Task", back_populates="user")

	roles = relationship(
		"Role",
		secondary=role_table,
		back_populates="users"
	)

	admin_orgs = relationship(
		"Organization",
		secondary=admin_user_table,
		back_populates="admin_users"
	)
	type = db.Column(db.String(50))

	def __init__(self, username, first_name, last_name, roles=None, ldap_guid=None, password=None):
		self.username = username.lower()
		self.first_name = first_name
		self.last_name = last_name
		self.ldap_guid = ldap_guid
		if password:
			self.set_password(password)
		self.gen_sync_username()

	#Needed flask properties
	@property
	def is_authenticated(self):
		return True

	@property
	def is_active(self):
		return True

	@property
	def is_anonymous(self):
		return False

	#password functions
	def set_password(self, password):
		self.password = generate_password_hash(password)

	def set_sync_password(self, password):
		self.sync_password = password
		for r in self.roles:
			for t in r.usertemplates:
				t.add_task(self)

	def start_sync(self):
		for r in self.roles:
			for t in r.usertemplates:
				t.add_task(self)

	def get_current_tasks(self):
		tasklist = []
		for t in self.tasks:
			tasklist.append(t)
		return tasklist

	def check_password(self, password):
		return check_password_hash(self.password, password)

	def get_id(self):
		return self.username

	def add_roles(self, *roles):
		self.roles.extend([role for role in roles if role not in self.roles])

	def add_role(self, role):
		self.roles.append(role)

	def check_role(self, role):
		if type(role) is str:
			rolelist = []
			for r in self.roles:
				rolelist.append(r.name)
			if role in rolelist:
				return True
		if role in self.roles:
			return True
	def gen_sync_username(self):
		self.sync_username = config.syncloginprefix + '-' + self.first_name + '.' + self.last_name

	def add_task(self, template, task_type='create'):
		self.tasks.append(Task(self, template, task_type))

	def add_to_org(self, org):
		self.admin_orgs.append(org)

	def disable(self):
		for r in self.roles:
			for t in r.usertemplates:
				t.add_task(self, task_type='disable')
		self.disabled = 'True'

	def enable(self):
		for r in self.roles:
			for t in r.usertemplates:
				t.add_task(self, task_type='enable')
		self.disabled = None

	def __repr__(self):
		return '<User %r>' % self.username




class Task(db.Model):
	__tablename__ = 'task'
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	task_type = db.Column(db.String(120))
	# organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
	# organization = relationship("Organization", uselist=False)
	template_id = db.Column(db.Integer, db.ForeignKey('user_template.id'))
	template = relationship("UserTemplate", uselist=False, back_populates="tasks")
	user = relationship("User", uselist=False, back_populates="tasks")
	created_at = db.Column(db.DateTime(timezone=True), default=func.now())
	status = relationship(
		"Status",
		secondary=status_map,
		uselist=False,
		back_populates="tasks"
	)

	def __init__(self, template, user, task_type='create'):
		self.template = template
		self.user = user
		self.task_type = task_type
		self.status = db.session.query(Status).filter_by(name='new').first()

	def __repr__(self):
		return '<Task ID {}>'.format(self.id)

	def change_status(self, status_id):
		try:
			status_id = int(status_id)
		except:
			self.status = status_id
		else:
			self.status = db.session.query(Status).filter_by(id=status_id).first()

class Organization(db.Model):
	__tablename__ = 'organization'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(120))
	admin_ou = db.Column(db.String(120))
	billing_group = db.Column(db.String(120))
	# tasks = relationship("Task")
	templates = relationship("UserTemplate", back_populates="organization")
	sync_key = db.Column(db.String(120))
	apikey = db.Column(db.String(120))
	billable_users = db.Column(db.Integer)
	disabled = db.Column(db.Boolean)
	admin_users = relationship(
		"User",
		secondary=admin_user_table,
		back_populates="admin_orgs"
	)
	# user_templates = relationship("UserTemplates", uselist=True, back_populates="organization")

	def __init__(self, name):
		self.name = name.lower()
		self.sync_key = crypt.genpass(32)
		self.add_template('Admin')
		self.gen_api_key()

	def __repr__(self):
		return '<Organization {}>'.format(self.name)

	def __str__(self):
		return self.name

	# def add_task(self, user):
	# 	self.tasks.append(Task(self, user))

	def gen_sync_key(self):
		self.sync_key = crypt.genpass(32)

	def gen_api_key(self):
		self.apikey = hexlify(os.urandom(18)).decode()

	def add_template(self, name):
		self.templates.append(UserTemplate(name))


class Status(db.Model):
	__tablename__="status"
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(120), unique=True)
	tasks = relationship(
		"Task",
		secondary=status_map,
		back_populates="status"
	)

	def __init__(self, id, name):
		self.id = id
		self.name = name

	def __repr__(self):
		return '<Status: {}>'.format(self.name)

	def __str__(self):
		return self.name


class UserTemplate(db.Model):
	__tablename__="user_template"
	id = db.Column(db.Integer, primary_key=True)
	organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
	organization = relationship("Organization", back_populates="templates")
	name = db.Column(db.String(120))
	user_ou = db.Column(db.String(120))
	disabled = db.Column(db.Boolean)
	single_attributes = relationship("SingleAttributes")
	multi_attributes = relationship("MultiAttributes")
	tasks = relationship("Task", back_populates="template")
	roles = relationship(
		"Role",
		secondary=role_template_map,
		back_populates="usertemplates"
	)

	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return '<Template: {}>'.format(self.name)

	def __str__(self):
		return self.name

	def add_single_attribute(self, key, value):
		self.single_attributes.append(SingleAttributes(key, value))

	def add_multi_attribute(self, key, value):
		self.multi_attributes.append(MultiAttributes(key, value))

	def add_role(self, role):
		self.roles.append(role)

	def add_task(self, user, task_type='create'):
		self.tasks.append(Task(self, user, task_type))

#
class SingleAttributes(db.Model):
	__tablename__="single_attributes"
	id = db.Column(db.Integer, primary_key=True)
	key = db.Column(db.String(120))
	value = db.Column(db.String(120))
	template = db.Column(db.Integer, db.ForeignKey('user_template.id'))


	def __init__(self, key, value):
		self.key = key
		self.value = value

	def __repr__(self):
		return '<Single_Attribute: {}: {}>'.format(self.key, self.value)

	def __str__(self):
		return self.name

class MultiAttributes(db.Model):
	__tablename__="multi_attributes"
	id = db.Column(db.Integer, primary_key=True)
	key = db.Column(db.String(120))
	value = db.Column(db.String(120))
	template = db.Column(db.Integer, db.ForeignKey('user_template.id'))


	def __init__(self, key, value):
		self.key = key
		self.value = value

	def __repr__(self):
		return '<Multi_Attribute: {}: {}>'.format(self.key, self.value)

	def __str__(self):
		return self.name