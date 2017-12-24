from flask import render_template, flash, redirect, url_for, request, jsonify
from app import app

@app.route('/home', methods=['GET'])
def home():
	app.logger.info("Someone viewed %s" % request.path)
	return "Hello World!"