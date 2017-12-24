from flask_sqlalchemy import SQLAlchemy
import logging
import config
from logging.handlers import RotatingFileHandler
from flask import Flask

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

handler = RotatingFileHandler(config.logfile, maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

from app import views, models