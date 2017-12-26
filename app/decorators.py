from functools import wraps
from werkzeug.exceptions import Forbidden

def import_user():
	try:
		from flask_login import current_user
		return current_user
	except ImportError:
		raise ImportError(
			'User argument not passed and current_user could not be imported.'
		)

def required(role):
	def wrapper(func):
		@wraps(func)
		def inner(*args, **kwargs):
			from .models import Role
			current_user = import_user()
			if role in current_user.roles:
				return func(*args, **kwargs)
			raise Forbidden("Your roles do not grant you access to this page")
		return inner
	return wrapper