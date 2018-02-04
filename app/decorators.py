from functools import wraps
from werkzeug.exceptions import Forbidden
from app import db, models
from flask import jsonify, request


def import_user():
	try:
		from flask_login import current_user
		return current_user
	except ImportError:
		raise ImportError(
			'User argument not passed and current_user could not be imported.'
		)


def api_auth(apikey, secret):
	sesh = db.session()
	try:
		org = sesh.query(models.Organization).filter_by(apikey=apikey).first()
		if org.apikey == apikey and org.sync_key == secret:
			return True
		else:
			return False
	except:
		sesh.rollback()
	finally:
		sesh.close()


def required(role):
	def wrapper(func):
		@wraps(func)
		def inner(*args, **kwargs):
			from .models import Role
			current_user = import_user()
			if current_user.check_role(role):
				return func(*args, **kwargs)
			raise Forbidden("Your roles do not grant you access to this page")
		return inner
	return wrapper


def api_key_required():
	def wrapper(func):
		@wraps(func)
		def inner(*args, **kwargs):
			apikey = request.args.get('apikey', default='', type=str)
			secret = request.args.get('secret', default='', type=str)
			if api_auth(apikey, secret) is True:
				return func(*args, **kwargs)
			return jsonify({"Error": "Incorrect authentication or not authorized."}), 401
		return inner
	return wrapper

# def dbcontext(func):
# 	def inner(*args, **kwargs):
# 		session = db.Session()
# 		try:
# 			func(*args, session=session, **kwargs)
# 			session.commit()
# 		except:
# 			session.rollback()
# 			raise
# 		finally:
# 			session.close()
# 	return inner