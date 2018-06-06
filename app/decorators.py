from functools import wraps
from werkzeug.exceptions import Forbidden
from app import db, models
from flask import jsonify, request
from mldapcommon.ldap_operations import LdapServerType, LdapOperations
from mldapcommon.errors import *
import config


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
			raise Forbidden("Your roles do not grant you access to this page, or your account is disabled.")
		return inner
	return wrapper

def no_disabled_users(func):
	@wraps(func)
	def inner(*args, **kwargs):
		current_user = import_user()
		if current_user.disabled:
			raise Forbidden("Your roles do not grant you access to this page, or your account is disabled.")
		else:
			return func(*args, **kwargs)
	return inner


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


def ldap_operation(func):
	@wraps(func)
	def inner(*args, **kwargs):
		ldap = LdapOperations(
				config.ldap_server_type,
				server=config.ldap_server,
				domain=config.ldap_domain,
				user=config.ldap_bind_user,
				plaintext_pw=config.ldap_bind_pw
			)
		try:
			return func(ldap, *args, **kwargs)
		except:
			raise
		finally:
			ldap.conn.unbind()
	return inner

def with_db_session(func):
	@wraps(func)
	def inner(*args, **kwargs):
		sesh = db.session()
		try:
			return func(sesh, *args, **kwargs)
		except:
			sesh.rollback()
			raise
		finally:
			sesh.close()
	return inner

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