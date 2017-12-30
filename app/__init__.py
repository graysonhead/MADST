from flask.ext.sqlalchemy import SQLAlchemy
import logging
import config
from logging.handlers import RotatingFileHandler
from flask import Flask, g
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_restful import Api


# Main flask app
app = Flask(__name__)
app.config.from_object('config')

# DB Object
db = SQLAlchemy(app)

db.init_app(app)
with app.test_request_context():
    db.create_all()

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Permissions
# perms = Permissions(app, db, current_user)


# API
api = Api(app)

# Logging
handler = RotatingFileHandler(config.logfile, maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

from app import views, views_api, models
