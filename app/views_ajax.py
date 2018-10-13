from flask import request
from flask import jsonify
from app import models, app, login_required, g
from .decorators import with_db_session
from .views_api import parse_task_item

@app.route('/api/ajax/tasks', methods=['get'])
@login_required
def ajax_tasks():
	tasks = []
	for task in g.user.tasks:
		tasks.append(parse_task_item(task))
	return jsonify(tasks)