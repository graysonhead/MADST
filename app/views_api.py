from flask_restful import reqparse, abort, Api, Resource
from app import api
from flask import jsonify
from app import db, models

# tasks = {
# 	'1': {
# 		'task': 'create',
# 		'username': 'Joe',
# 		'password': 'lmfao'
# 		}
# }
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
				'sync_password': val.user.sync_password
			}

		}
	except:
		sesh.rollback()
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
					'sync_password': val.user.sync_password
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

parser = reqparse.RequestParser()
parser.add_argument('task')

class Task(Resource):
	def get(self, task_id):
		task = get_task(task_id)
		return task

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