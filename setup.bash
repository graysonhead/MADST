#!/bin/bash
yum install python34 python34-devel python34-crypto python34-pip gcc make -y
python3 -m venv ./venv
./venv/bin/pip3 install Flask Flask-Login Flask-RESTful Flask-SQLAlchemy Flask-WTF SQLAlchemy sqlalchemy-migrate WTForms pycrypto requests 

