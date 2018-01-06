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

def get_tasks():
	sesh = db.session()
	try:
		tasks = {}
		db_tasks = sesh.query(models.Task).all()
		for i, val in enumerate(db_tasks):
			task_item = {
				'id': val.id,
				'is_complete': val.is_complete,
				'is_sent': val.is_sent,
				'user_id': val.user_id,
				'organization_id': val.organization_id,
				'username': val.user.username,
				'first_name': val.user.first_name.title(),
				'last_name': val.user.last_name.title(),
				'sync_username': val.user.sync_username,
				'sync_password': val.user.sync_password
			}
			tasks.update({str(i): task_item})
	except:
		sesh.rollback()
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
		tasks = get_tasks()
		abort_no_task(task_id)
		return tasks[task_id]


class Tasks(Resource):
	def get(self):
		tasks = get_tasks()
		return tasks

class Tasks_Count(Resource):
	def get(self):
		tasks = get_tasks()
		return { 'count': len(tasks)}



api.add_resource(Tasks_Count, '/api/tasks/count')
api.add_resource(Tasks, '/api/tasks')
api.add_resource(Task, '/api/task/<task_id>')
api.add_resource(Tasks, )