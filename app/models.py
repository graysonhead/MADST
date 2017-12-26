from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.permissions.models import UserMixin, Role, Ability
import datetime
from hashlib import md5

# @rbac.as_role_model
# class Role(db.Model,):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(20))
#
#
#     def __init__(self, name):
#         RoleMixin.__init__(self)
#         self.name = name
#
#     def add_parent(self, parent):
#         # You don't need to add this role to parent's children set,
#         # relationship between roles would do this work automatically
#         self.parents.append(parent)
#
#     def add_parents(self, *parents):
#         for parent in parents:
#             self.add_parent(parent)
#
#     @staticmethod
#     def get_by_name(name):
#         return Role.query.filter_by(name=name).first()
#
class BRole(Role):
	def __init__(self, name):
		Role.__init__(self, name)


class User(UserMixin):
	username = db.Column(db.String(120), unique=True)
	password = db.Column(db.String(120))

	def __init__(self, username, password, roles=None):
		self.username = username.lower()
		self.set_password(password)
		# Be sure to call the UserMixin's constructor in your class constructor
		UserMixin.__init__(self, roles)

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

	def __repr__(self):
		return '<User %r>' % self.username




