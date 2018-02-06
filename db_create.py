#!venv/bin/python
from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from app import db
import os.path

db.create_all()
if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
	api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
	api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
else:
	api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO,
						api.version(SQLALCHEMY_MIGRATE_REPO))

from app import db, models
""" Pre-Populate Statuses """
sesh = db.session()
try:
	new = models.Status(1, 'new')
	inprogress = models.Status(2, 'in progress')
	completed = models.Status(3, 'completed')
	failed = models.Status(4, 'failed')
	failedbattr = models.Status(5, 'failed: bad attribute')
	sesh.add(new)
	sesh.add(inprogress)
	sesh.add(completed)
	sesh.add(failed)
	sesh.add(failedbattr)
	sesh.commit()
except:
	sesh.rollback()
	raise
finally:
	sesh.close()
""" Add admin user """
sesh = db.session()
try:
	user = models.User('admin', 'admin', 'admin', 'user', roles='Admin')
	sesh.add(user)
	sesh.commit()
except:
	sesh.rollback()
	raise
finally:
	sesh.close()

print("DB Initialized")