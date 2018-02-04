from flask import request
from flask import jsonify
from app import db, models, crypt, app
from .decorators import api_key_required
import re


def atrib_regex(username, firstname, lastname, string):
	''' Perform string replacement on Attribute values '''
	string = re.sub(r"%userName%", username, string)
	string = re.sub(r"%firstName%", firstname, string)
	return re.sub(r"%lastName%", lastname, string)


def tasks_fetch(org_id=False):
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
						task_item['attributes']['single_attributes'].update({s.key: atrib_regex(val.user.sync_username,
																								val.user.first_name,
																								val.user.last_name,
																								s.value)})
			except IndexError:
				pass
			try:
				if val.organization.templates[0].multi_attributes[0]:
					for s in val.organization.templates[0].multi_attributes:
						task_item['attributes']['multi_attributes'].update({s.key: atrib_regex(val.user.sync_username,
																							   val.user.first_name,
																							   val.user.last_name,
																							   s.value)})
			except IndexError:
				pass
			tasks.update({str(i): task_item})
		return tasks
	except:
		sesh.rollback()
	finally:
		sesh.close()


def task_fetch(task_id):
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


@app.route('/api/task/<task_id>', methods=['GET', 'PUT', 'POST'])
@api_key_required()
def api_task(task_id):
	# Begin GET block
	if request.method == 'GET':
		return jsonify(task_fetch(task_id))
	# End GET block
	# Begin PUT block
	elif request.method == 'PUT':
		try:
			data = request.get_json()
			status_id = data['status']
		except AttributeError:
			return jsonify({"Error": "Bad request data", "RequestData": data}), 406
		except KeyError:
			return jsonify({"Error": "A non-optional key is missing, please check the documentation and try again", "RequestData": data}), 406
		sesh = db.session()
		try:
			taskdb = sesh.query(models.Task).filter_by(id=task_id).first()
			try:
				taskdb.change_status(status_id)
			except:
				return jsonify({"Error": "No status code {} exists".format(status_id)}), 404
			sesh.add(taskdb)
			sesh.commit()
		except:
			sesh.rollback()
			return jsonify({"Error": "There is no task with id{}".format(task_id)}), 404
		finally:
			sesh.close()
		return jsonify(task_fetch(task_id)), 201

@app.route('/api/tasks', methods=['GET'])
@api_key_required()
def get_tasks(org_id=False):
	org_id = request.args.get('org_id', default='', type=int)
	# Begin GET block
	if request.method == 'GET':
		if org_id:
			tasks = tasks_fetch(org_id)
			if tasks:
				return jsonify(tasks)
			else:
				return jsonify({"Error": "Organization doesn't exist"}), 404
		else:
			return jsonify(tasks_fetch())
	# End GET block
