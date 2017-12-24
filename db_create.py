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

'''
contrib = models.Contributor(first_name = 'Fat', last_name = 'Murderer', email = 'fuckingbitches@gmail.com')
db.session.add(contrib)
db.session.commit()
cntrb1 = db.session.query(models.Contributor).filter_by(email='fuckingbitches@gmail.com').first()
course = models.Course(contributor_id = cntrb1.id, name = 'Get Swole with the Fat Murderer')
db.session.add(course)
db.session.commit()
crs1 = db.session.query(models.Course).filter_by(name = 'Get Swole with the Fat Murderer').first()
class1 = models.Classes(course_id = crs1.id, name = 'Get Swole: week 1', description = 'This week, we are going to focus on getting swole', video_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ')
db.session.add(class1)
db.session.commit()
contrib_lmbm = models.Contributor(first_name = 'lance', last_name = 'McBuffMuscles', email = 'iloveprotienpowder@gmail.com')
db.session.add(contrib_lmbm)
db.session.commit()
cntrb2 = db.session.query(models.Contributor).filter_by(email='iloveprotienpowder@gmail.com').first()
course_lmbm = models.Course(contributor_id = cntrb2.id, name = 'Advanced upper Body Techniques', description = 'Get the arms, chest, and shallow woman you\'ve always dreamed of!')
db.session.add(course_lmbm)
db.session.commit()
'''
