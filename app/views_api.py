from flask import request
from flask import jsonify
from app import db, models, crypt, app
from .decorators import api_key_required, with_db_session
import re


def parse_task_item(task):
	task_item = {
		'id': task.id,
		'type': 'create',
		'status': {
			'id': task.status.id,
			'name': task.status.name
		},
		'organization': {
			'id': task.organization_id,
			'name': task.organization.name,
			'admin_ou': task.organization.admin_ou
		},
		'user': {
			'first_name': task.user.first_name.title(),
			'last_name': task.user.last_name.title(),
			'sync_username': task.user.sync_username,
			'sync_password': crypt.encrypt(task.user.sync_password, task.organization.sync_key).decode('utf-8')
		},
		'attributes': {
			'single_attributes': {},
			'multi_attributes': {}
		}
	}
	try:
		if task.organization.templates[0].single_attributes[0]:
			for s in task.organization.templates[0].single_attributes:
				task_item['attributes']['single_attributes'].update({s.key: atrib_regex(task.user.sync_username,
																						task.user.first_name,
																						task.user.last_name,
																						s.value)})
	except IndexError:
		pass
	try:
		if task.organization.templates[0].multi_attributes[0]:
			for s in task.organization.templates[0].multi_attributes:
				if s.key in task_item['attributes']['multi_attributes']:
					task_item['attributes']['multi_attributes'][s.key].append(atrib_regex(task.user.sync_username,
																						  task.user.first_name,
																						  task.user.last_name,
																						  s.value))
				else:
					task_item['attributes']['multi_attributes'][s.key] = [(atrib_regex(task.user.sync_username,
																					   task.user.first_name,
																					   task.user.last_name,
																					   s.value))]
	except IndexError:
		pass
	return task_item


def atrib_regex(username, firstname, lastname, string):
	''' Perform string replacement on Attribute values '''
	string = re.sub(r"%userName%", username, string)
	string = re.sub(r"%firstName%", firstname, string)
	return re.sub(r"%lastName%", lastname, string)


def org_not_exist():
	return jsonify({"Error": "Organization doesn't exist"}), 404

def bad_request_data(data):
	return jsonify({"Error": "Bad request data", "RequestData": data}), 406

def get_billable_users(sesh, org_id):
	org = sesh.query(models.Organization).filter_by(id=org_id).first()
	return org.billable_users


def tasks_fetch(sesh, org_id=False):
	tasks = {}
	if org_id:
		db_tasks = sesh.query(models.Task).filter_by(organization_id=org_id).all()
	else:
		db_tasks = sesh.query(models.Task).all()
	for i, val in enumerate(db_tasks):
		task_item  = parse_task_item(val)
		tasks.update({str(i): task_item})
	return tasks



def task_fetch(sesh, task_id):
	val = sesh.query(models.Task).filter_by(id=task_id).first()
	return parse_task_item(val)


@app.route('/api/task/<task_id>', methods=['GET', 'PUT', 'POST'])
@api_key_required()
@with_db_session
def api_task(sesh, task_id):
	# Begin GET block
	if request.method == 'GET':
		return jsonify(task_fetch(sesh, task_id))
	# End GET block
	# Begin PUT block
	elif request.method == 'PUT':
		try:
			data = request.get_json()
			status_id = data['status']
		except AttributeError:
			return bad_request_data(data)
		except KeyError:
			return jsonify({"Error": "A non-optional key is missing, please check the documentation and try again", "RequestData": data}), 406

		taskdb = sesh.query(models.Task).filter_by(id=task_id).first()
		try:
			taskdb.change_status(status_id)
		except:
			return jsonify({"Error": "No status code {} exists".format(status_id)}), 404
		sesh.add(taskdb)
		sesh.commit()
		return jsonify(task_fetch(sesh, task_id)), 201
	# End PUT block

@app.route('/api/tasks', methods=['GET'])
@api_key_required()
@with_db_session
def get_tasks(sesh, org_id=False):
	org_id = request.args.get('org_id', default='', type=int)
	# Begin GET block
	if request.method == 'GET':
		if org_id:
			tasks = tasks_fetch(sesh, org_id)
			if tasks:
				return jsonify(tasks)
			else:
				return org_not_exist()
		else:
			return jsonify(tasks_fetch(sesh))
	# End GET block

@app.route('/api/org/users/count', methods=['GET', 'PUT'])
@api_key_required()
@with_db_session
def api_org_usercount(sesh):
	# Begin GET block
	org_id = request.args.get('org_id', default=0, type=int)
	if request.method == 'GET':
		try:
			billable_users = get_billable_users(sesh, org_id)
		except:
			return jsonify({"Error": "An internal server error occured"}), 500
		if billable_users:
			return jsonify({"Billable_Users": billable_users})
		else:
			return org_not_exist()
	# End GET block
	# Begin PUT block
	elif request.method == 'PUT':
		try:
			data = request.get_json()
			billable_users = data['billable_users']
		except AttributeError:
			return bad_request_data(data)
		except KeyError:
			return jsonify({"Error": "A non-optional key is missing, please check the documentation and try again", "RequestData": data}), 406
		org = sesh.query(models.Organization).filter_by(id=org_id).first()
		if org is None:
			return org_not_exist()
		org.billable_users = billable_users
		sesh.add(org)
		sesh.commit()
		return jsonify({"Billable_Users": get_billable_users(sesh, org_id)})

	#end PUT block


