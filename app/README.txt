start up a python3 VENV (named venv, if you want to use run.py without modification)

You will need to install the following packages:

flask
flask-login
flask-permissions
flask-sqlalchemy
flask-WTF
Werkzeug
sqlalchemy-migrate


#DB Setup scratch

new = models.Status('new')
in_progress = models.Status('in progress')
completed = models.Status('completed')
failed = models.Status('failed')
sesh = db.session()
sesh.add(new)
sesh.add(in_progress)
sesh.add(completed)
sesh.add(failed)