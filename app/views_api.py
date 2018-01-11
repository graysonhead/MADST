from flask_restful import reqparse, abort, Api, Resource
from app import api
from flask import jsonify
from app import db, models, crypt

def get_task(id):
	sesh = db.session
	try:
		val = sesh.query(models.Task).filter_by(id=id).first()
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
			}

		}
	except:
		sesh.rollback()
		raise
	finally:
		sesh.close()
	return task_item


def get_tasks(org_id=False):
	sesh = db.session()
	try:
		tasks = {}
		if org_id:
			db_tasks = sesh.query(models.Task).filter_by(organization_id=org_id).all()
		else:
			db_tasks = sesh.query(models.Task).all()
		for i, val in enumerate(db_tasks):
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
				}


			}
			tasks.update({str(i): task_item})
	except:
		sesh.rollback()
		raise
	finally:
		sesh.close()
		return tasks


def abort_no_task(task_id):
	if task_id not in tasks:
		abort(404, message="Task {} doesn't exist".format(task_id))

def abort_no_status(status_id):
	abort(404, message="Status {} doesn't exist".format(status_id))


parser = reqparse.RequestParser()
parser.add_argument('status')


class Task(Resource):
	def get(self, task_id):
		task = get_task(task_id)
		return task

	def put(self, task_id):
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
		tasks = get_tasks()
		return tasks

class Tasks_filtered(Resource):
	def get(self, org_id):
		tasks = get_tasks(org_id)
		return tasks

class Tasks_Count(Resource):
	def get(self):
		tasks = get_tasks()
		return { 'count': len(tasks)}



api.add_resource(Tasks_Count, '/api/tasks/count')
api.add_resource(Tasks, '/api/tasks')
api.add_resource(Tasks_filtered, '/api/tasks/<org_id>')
api.add_resource(Task, '/api/task/<task_id>')
api.add_resource(Tasks, )