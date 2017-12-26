from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.associationproxy import association_proxy
import datetime
from hashlib import md5

role_table = db.Table('user_role',
					  db.Column(
						  'user_id', db.Integer, db.ForeignKey('user.id')
					  ),
					  db.Column(
						  'role_id', db.Integer, db.ForeignKey('role.id')
					  )
					  )

class Role(db.Model):
	__tablename__ = 'role'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(120), unique=True)

	def __init__(self, name):
		self.name = name.lower()

	def __repr__(self):
		return '<Role {}>'.format(self.name)

	def __str__(self):
		return self.name


class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(120), unique=True)
	password = db.Column(db.String(120))
	__tablename__ = 'user'
	_roles = db.relationship(
		'Role', secondary=role_table, backref='users'
	)
	type = db.Column(db.String(50))

	roles = association_proxy('_roles', 'name')

	def __init__(self, username, password, roles=None):
		self.username = username.lower()
		self.set_password(password)

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

	def check_password(self, password):
		return check_password_hash(self.password, password)

	def get_id(self):
		return self.username

	def check_role(self, role):
		if role in self.roles:
			return 'Truth'

	def __repr__(self):
		return '<User %r>' % self.username




