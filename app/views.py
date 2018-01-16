from flask import render_template, flash, redirect, url_for, request
from app import app, db, models, g, login_manager, login_user, logout_user, login_required, current_user
from .decorators import required
from .forms import LoginForm, PasswordChange, AddName, AttributesForm, KeyValue

# from flask.ext.permissions.decorators import user_is, user_has


def log_pageview(request):
	app.logger.info("Someone viewed %s" % request)


@login_manager.user_loader
def load_user(username):
	return db.session.query(models.User).filter_by(username=username).first()


@app.before_request
def before_request():
	g.user = current_user


@required('Technician')
@login_required
@app.route('/index', methods=['GET', 'POST'])
def index():
	form = PasswordChange()
	if form.password.data:
		password = form.password.data
		sesh = db.session()
		try:
			user = sesh.query(models.User).filter_by(id=g.user.id).first()
			user.set_sync_password(password)
			sesh.add(user)
			app.logger.info("{} changed their sync password".format(g.user.username))
			flash("Sync password changed.")
		except:
			flash("Sync Password change failed.")
			sesh.rollback()
			raise
		finally:
			sesh.commit()
			sesh.close()
			return redirect(url_for('index'))
	if not g.user.is_authenticated:
		return(redirect(url_for('login')))
	log_pageview(request.path)
	if g.user.first_name and g.user.last_name:
		friendly_name = g.user.first_name + ' ' + g.user.last_name
	else:
		friendly_name = g.user.username
	# Build task list

	return render_template(
		'home.html',
		friendly_name=friendly_name.title(),
		user=g.user,
		form=form,
		title='Home'
	)

@required('Admin')
@login_required
@app.route('/admin/orgs', methods=['GET'])
def admin_orgs():
	""" Displays list of organizations and allows you to navigate to their respective admin pages"""
	sesh = db.session()
	try:
		orgs = sesh.query(models.Organization).all()
	except:
		sesh.rollback()
	finally:
		sesh.close()
	return render_template(
		'admin_orgs.html',
		title='Organization Admin',
		orgs=orgs
	)

@required('Admin')
@login_required
@app.route('/admin/org', methods=['GET', 'POST'])
def admin_org():
	""" Allows viewing and modification of Organization Attributes"""
	org_id = request.args.get('org_id', default = 1, type = int)
	form = AddName()
	if form.name.data:
		sesh = db.session()
		try:
			org = sesh.query(models.Organization).filter_by(id=org_id).first()
			org.add_template(form.name.data)
			sesh.add(org)
			sesh.commit()
			flash("Added {} to {}".format(form.name.data, org.name))
		except:
			sesh.rollback()
			flash("DB write failed", 'error')
		finally:
			sesh.close()
		return(redirect(url_for("admin_org")))
	sesh = db.session()
	try:
		org = sesh.query(models.Organization).filter_by(id=org_id).first()
		templates = org.templates
	except:
		sesh.rollback()
	finally:
		sesh.close()


	return render_template(
		'admin_org.html',
		form=form,
		title='Organization Admin: {}'.format(org.name.title()),
		org=org,
		templates=templates
	)

@required('Admin')
@login_required
@app.route('/admin/org/template', methods=['GET'])
def admin_org_template(**kwargs):
	""" Allows viewing and modification of Organization Attributes"""
	sesh = db.session()
	""" Forms """
	form = AddName()
	svform = AttributesForm()
	kvform = KeyValue()
	""" Template will replace selected attribute with a form allowing for editing """
	selected_single_attribute = request.args.get('selected_single_attribute', default=0, type=int)
	try:
		template = sesh.query(models.UserTemplate).filter_by(id=request.args.get('template_id', default=1, type=int)).first()
		org = sesh.query(models.Organization).filter_by(id=template.organization).first()
		templates = org.templates
		single_attributes = template.single_attributes
	except:
		sesh.rollback()
	finally:
		sesh.close()

	return render_template(
		'admin_org_template.html',
		form=form,
		svform=svform,
		kvform=kvform,
		single_attributes=single_attributes,
		title='Template Admin: {} ({})'.format(template.name.title(), org.name.title()),
		org=org,
		templates=templates,
		selected_single_attribute=selected_single_attribute,
		template=template
	)

@app.route('/sec1', methods=['GET'])
@required('Technician')
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

