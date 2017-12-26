from flask_sqlalchemy import SQLAlchemy
import logging
import config
from logging.handlers import RotatingFileHandler
from flask import Flask, g
from flask_login import LoginManager, login_user, logout_user, current_user, login_required

# Main flask app
app = Flask(__name__)
app.config.from_object('config')

# DB Object
db = SQLAlchemy(app)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Logging
handler = RotatingFileHandler(config.logfile, maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

from app import views, models
