from flask_sqlalchemy import SQLAlchemy
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, g
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_restful import Api
import jinja2
import sys
#from .sync import sync_roles
import time
import atexit

# from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask_apscheduler import APScheduler

from mldapcommon import ldap_operations

version_number = 'Beta 0.4.2'
try:
	import config
except ImportError:
	print("Copy the example config file and ensure it is named 'config.py'")
	sys.exit(1)

# Main flask app
app = Flask(__name__)
app.config.from_object('config')
#app.jinja_env.undefined = jinja2.StrictUndefined

# DB Object
db = SQLAlchemy(app)

db.init_app(app)
with app.test_request_context():
	db.create_all()

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#Shared LDAP bind for searching

# Permissions
# perms = Permissions(app, db, current_user)


# API
api = Api(app)

# Logging
formatter = logging.Formatter(
        "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
handler = RotatingFileHandler(config.logfile, maxBytes=10000, backupCount=1)
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)




# Scheduled Tasks
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

from app import views, views_api, models

