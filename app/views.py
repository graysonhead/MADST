from flask import render_template, flash, redirect, url_for, request
from app import app, db, models, g, login_manager, login_user, logout_user, login_required, current_user
from .decorators import required
from .forms import LoginForm

# from flask.ext.permissions.decorators import user_is, user_has


def log_pageview(request):
	app.logger.info("Someone viewed %s" % request)

@login_manager.user_loader
def load_user(username):
	return db.session.query(models.User).filter_by(username=username).first()


@app.before_request
def before_request():
	g.user = current_user



@app.route('/index', methods=['GET'])
def index():
	log_pageview(request.path)
	return render_template(
		'home.html',
		title='Home'
	)

@app.route('/sec1', methods=['GET'])
@required('admin')
@login_required
def sec1():
	log_pageview(request.path)
	return "Secure page 1"



@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if g.user is not None and g.user.is_authenticated:
		return redirect(url_for('index'))
	if form:
		username = form.username.data
		password = form.password.data
		remember_me = form.remember_me.data
		userObj = db.session.query(models.User).filter_by(username=username).first()
		if userObj:
			passval = userObj.check_password(password)
			if passval:
				app.logger.info("User %s logged in" % userObj.username)
				login_user(userObj, remember=remember_me)
				g.current_user = userObj
				flash('You have logged in successfully')
				return redirect(url_for('index'))
			else:
				app.logger.info('User {0} attempted to login with incorrect password'.format(form.username.data))
				flash("Incorrect password")
		else:
			app.logger.info('User attempted to login with unknown username {0}'.format(form.username.data))
			flash("Incorrect username")
	return render_template('login.html',
						   title='Sign In',
						   form=form)


@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for('index'))

