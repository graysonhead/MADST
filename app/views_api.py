from flask_restful import reqparse, abort, Api, Resource
from app import api
from flask import jsonify
from app import db, models, crypt
import re
from functools import wraps

key_parser = reqparse.RequestParser()
key_parser.add_argument('apikey')
key_parser.add_argument('secret')


def api_auth(apikey, secret):
	sesh = db.session()
	try:
		org = sesh.query(models.Organization).filter_by(apikey=apikey).first()
		if org.apikey == apikey and org.sync_key == secret:
			return False
		else:
			return True
	except:
		sesh.rollback()
	finally:
		sesh.close()


def atrib_regex(username, firstname, lastname, string):
	''' Perform string replacement on Attribute values '''
	string = re.sub(r"%userName%", username, string)
	string = re.sub(r"%firstName%", firstname, string)
	return re.sub(r"%lastName%", lastname, string)


def get_task(task_id):
	sesh = db.session
	try:
		val = sesh.query(models.Task).filter_by(id=task_id).first()
		task_item = {
			'id': val.id,
			'status': {
				'id': val.status.id,
				'name': val.status.name
			},
			'organization': {
				'id': val.organization_id,
				'name': val.organization.name,
				'admin_ou': val.organization.admin_ou
			},
			'user': {
				'first_name': val.user.first_name.title(),
				'last_name': val.user.last_name.title(),
				'sync_username': val.user.sync_username,
				'sync_password': crypt.encrypt(val.user.sync_password, val.organization.sync_key).decode('utf-8')
			},
		'attributes': {
			'single_attributes': {},
			'multi_attributes': {}
			}
		}
		try:
			if val.organization.templates[0].single_attributes[0]:
				for s in val.organization.templates[0].single_attributes:
					task_item['attributes']['single_attributes'].update({s.key: atrib_regex(val.user.sync_username, val.user.first_name, val.user.last_name, s.value)})
		except IndexError:
			pass
		try:
			if val.organization.templates[0].multi_attributes[0]:
				for s in val.organization.templates[0].multi_attributes:
					task_item['attributes']['multi_attributes'].update({s.key: atrib_regex(val.user.sync_username, val.user.first_name, val.user.last_name, s.value)})
		except IndexError:
			pass
	except:
		sesh.rollback()
		raise
	finally:
		sesh.close()
	return task_item


def get_tasks(org_id=False):
	sesh = db.session()
	args = key_parser.parse_args()
	try:
		# Check for auth
		tasks = {}
		if org_id:
			db_tasks = sesh.query(models.Task).filter_by(organization_id=org_id).all()
		else:
			db_tasks = sesh.query(models.Task).all()
		for i, val in enumerate(db_tasks):
			task_item = {
				'id': val.id,
				'type': 'create',
				'status': {
					'id': val.status.id,
					'name': val.status.name
				},
				'organization': {
					'id': val.organization_id,
					'name': val.organization.name,
					'admin_ou': val.organization.admin_ou
				},
				'user': {
					'first_name': val.user.first_name.title(),
					'last_name': val.user.last_name.title(),
					'sync_username': val.user.sync_username,
					'sync_password': crypt.encrypt(val.user.sync_password, val.organization.sync_key).decode('utf-8')
				},
				'attributes': {
					'single_attributes': {},
					'multi_attributes': {}
				}
			}
			try:
				if val.organization.templates[0].single_attributes[0]:
					for s in val.organization.templates[0].single_attributes:
							task_item['attributes']['single_attributes'].update({s.key: atrib_regex(val.user.sync_username, val.user.first_name, val.user.last_name, s.value)})
			except IndexError:
				pass
			try:
				if val.organization.templates[0].multi_attributes[0]:
					for s in val.organization.templates[0].multi_attributes:
							task_item['attributes']['multi_attributes'].update({s.key: atrib_regex(val.user.sync_username, val.user.first_name, val.user.last_name, s.value)})
			except IndexError:
				pass
			tasks.update({str(i): task_item})
			return tasks
		else:
			return {"Error": "Incorrect authentication or not authorized."}
	except:
		sesh.rollback()
		return {"Error": "True"}
	finally:
		sesh.close()



def abort_no_task(task_id):
	if task_id not in tasks:
		abort(404, message="Task {} doesn't exist".format(task_id))

def abort_no_status(status_id):
	abort(404, message="Status {} doesn't exist".format(status_id))


parser = reqparse.RequestParser()
parser.add_argument('status')


class Task(Resource):
	def get(self, task_id):
		keyargs = key_parser.parse_args()
		if api_auth(keyargs['apikey'], keyargs['secret']):
			return {"Error": True, "Message": "Auth Failure"}
		task = get_task(task_id)
		return task

	def put(self, task_id):
		keyargs = key_parser.parse_args()
		if api_auth(keyargs['apikey'], keyargs['secret']):
			return {"Error": True, "Message": "Auth Failure"}
		args = parser.parse_args()
		sesh = db.session()
		try:
			taskdb = sesh.query(models.Task).filter_by(id=task_id).first()
			try:
				taskdb.change_status(args['status'])
			except:
				return abort_no_status(args['status'])
			sesh.add(taskdb)
			sesh.commit()
		except:
			sesh.rollback()
			return abort_no_task(task_id)
		finally:
			sesh.close()
		return get_task(task_id), 201
	# def put(self, task_id):
	# 	args = parser.parse_args()


class Tasks(Resource):
	def get(self):
		keyargs = key_parser.parse_args()
		if api_auth(keyargs['apikey'], keyargs['secret']):
			return {"Error": True, "Message": "Auth Failure"}
		tasks = get_tasks()
		return tasks


class Tasks_filtered(Resource):
	def get(self, org_id):
		keyargs = key_parser.parse_args()
		if api_auth(keyargs['apikey'], keyargs['secret']):
			return {"Error": True, "Message": "Auth Failure"}
		tasks = get_tasks(org_id)
		return tasks

class Tasks_Count(Resource):
	def get(self):
		keyargs = key_parser.parse_args()
		if api_auth(keyargs['apikey'], keyargs['secret']):
			return {"Error": True, "Message": "Auth Failure"}
		tasks = get_tasks()
		return { 'count': len(tasks)}



api.add_resource(Tasks_Count, '/api/tasks/count')
api.add_resource(Tasks, '/api/tasks')
api.add_resource(Tasks_filtered, '/api/tasks/<org_id>')
api.add_resource(Task, '/api/task/<task_id>')
api.add_resource(Tasks, )