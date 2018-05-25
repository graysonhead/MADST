#!/bin/bash
if [ -f "/etc/redhat-release"]; then
	yum install python34 python34-devel python34-crypto python34-pip gcc make -y
elif [ -f "/etc/debian_version" ]; then
	apt install python3 python3-dev python3-pip python3-venv gcc make -y
python3 -m venv ./venv
fi
./venv/bin/pip3 install Flask Flask-Login Flask-RESTful Flask-SQLAlchemy Flask-WTF SQLAlchemy sqlalchemy-migrate WTForms pycrypto requests 
