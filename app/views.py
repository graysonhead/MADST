from flask import render_template, flash, redirect, url_for, request
from app import app, db, models, g, login_manager, login_user, logout_user, login_required, current_user, version_number
from .decorators import required
from .forms import \
	LoginForm, \
	PasswordChange, \
	AddName, \
	KeyValueAdd, \
	KeyValueModify, \
	MultiKeyValueAdd, \
	MultiKeyValueModify, \
	UserCreationForm, \
	AddAdminUser

# from flask.ext.permissions.decorators import user_is, user_has


def delete_user(user_id):
	sesh = db.session()
	try:
		user = sesh.query(models.User).filter_by(id=user_id).first()
		sesh.delete(user)
		sesh.commit()
	except:
		sesh.rollback()
	finally:
		sesh.close()

def create_user(username, first_name, last_name, password):
	sesh = db.session()
	try:
		user = models.User(username, password, first_name.lower(), last_name.lower())
		sesh.add(user)
		sesh.commit()
	except:
		sesh.rollback()
	finally:
		sesh.close()


def get_user(user_id):
	sesh = db.session()
	try:
		return sesh.query(models.User).filter_by(id=user_id).first()
	except:
		sesh.rollback()
	finally:
		sesh.close()


def get_users():
	sesh = db.session()
	try:
		return sesh.query(models.User).all()
	except:
		sesh.rollback()
	finally:
		sesh.close()


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
		version_number=version_number,
		title='Home'
	)


@required('Admin')
@login_required
@app.route('/admin/orgs', methods=['GET', 'POST'])
def admin_orgs():
	""" Displays list of organizations and allows you to navigate to their respective admin pages"""
	form = AddName()
	if request.method == 'POST':
		name = form.name.data
		sesh = db.session()
		try:
			org = models.Organization(name)
			sesh.add(org)
			sesh.commit()
			flash('Added new organization {}.'.format(name))
		except:
			sesh.rollback()
			flash('Failed to add new organization {}.'.format(name))
			raise
		finally:
			sesh.close()
		return (redirect(url_for('admin_orgs')))
	if request.method == 'GET':
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
			form=form,
			version_number=version_number,
			orgs=orgs
		)


@required('Admin')
@login_required
@app.route('/admin', methods=['GET'])
def admin():
	return render_template(
		'admin.html',
		version_number=version_number,
		title='Admin'
	)


@required('Admin')
@login_required
@app.route('/admin/org', methods=['GET', 'POST'])
def admin_org():
	""" Allows viewing and modification of Organization Attributes"""
	org_id = request.args.get('org_id', default=1, type=int)
	delete = request.args.get('delete', default=0, type=int)
	resync = request.args.get('resync', default=0, type=int)
	form = AddName()
	userform = AddAdminUser()
	# Begin POST block
	if request.method == 'POST':
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
		elif userform.adminname.data:
			sesh = db.session()
			try:
				org = sesh.query(models.Organization).filter_by(id=org_id).first()
				user = sesh.query(models.User).filter_by(username=userform.adminname.data).first()
				if not user:
					flash("User {} not found".format(user.username))
					return(redirect(url_for("admin_org", org_id = org_id)))
				user.add_to_org(org)
				sesh.add(org)
				sesh.add(user)
				sesh.commit()
				flash("Added admin user {} to org {}".format(user.username, org.name))
			except:
				sesh.rollback()
				flash("Failed to add user {} to org {}".format(user.username, org.name))
			finally:
				sesh.close()
		return(redirect(url_for("admin_org", org_id = org_id)))
	# End POST block
	# Begin GET block
	if request.method == 'GET':
		if delete == 1:
			sesh = db.session()
			try:
				org = sesh.query(models.Organization).filter_by(id=org_id).first()
				for tmp in org.templates:
					# Clean up single attributes in org
					for sa in tmp.single_attributes:
						sesh.delete(sa)
					# Clean up multi attributes in org
					for ma in tmp.multi_attributes:
						sesh.delete(ma)
					# Clean up templates in org
					sesh.delete(tmp)
				# Clean up tasks in org
				for t in org.tasks:
					sesh.delete(t)
				# Delete org
				sesh.delete(org)
				sesh.commit()
				flash("Deleted organization {}.".format(org.name))
			except:
				sesh.rollback()
				flash("Database error occurred while deleting organization {}".format(org.name))
			finally:
				sesh.close()
			return(redirect(url_for('admin_orgs')))
		elif resync == 1:
			sesh = db.session()
			try:
				org = sesh.query(models.Organization).filter_by(id=org_id).first()
				for u in org.admin_users:
					org.add_task(u)
				flash("Created sync tasks for all admin users in organization {}".format(org.name))
				sesh.commit()
			except:
				sesh.rollback()
			finally:
				sesh.close()
			return(redirect(url_for('admin_org', org_id=org_id)))
		sesh = db.session()
		try:
			org = sesh.query(models.Organization).filter_by(id=org_id).first()
			templates = org.templates
			admin_users = org.admin_users
		except:
			sesh.rollback()
		finally:
			sesh.close()
		return render_template(
			'admin_org.html',
			form=form,
			userform=userform,
			title='Organization Admin: {}'.format(org.name.title()),
			org=org,
			admin_users=admin_users,
			version_number=version_number,
			templates=templates
		)
	#End GET block


@required('Admin')
@login_required
@app.route('/admin/org/template', methods=['GET', 'POST'])
def admin_org_template(**kwargs):
	""" Allows viewing and modification of Organization Attributes"""
	selected_single_attribute = request.args.get('selected_single_attribute', default=0, type=int)
	selected_multi_attribute = request.args.get('selected_multi_attribute', default=0, type=int)
	template_id = request.args.get('template_id', default=1, type=int)
	delete = request.args.get('delete', default=0, type=int)
	""" Forms """
	svform = KeyValueModify()
	new_sv_form = KeyValueAdd()
	form = AddName()
	mvform = MultiKeyValueModify()
	new_mvform = MultiKeyValueAdd()

	if request.method == 'POST':
		template_id = request.args.get('template_id', default=1, type=int)
		""" Single Value Logic """
		if svform.mod_key.data or svform.mod_delete.data == True:
			sesh = db.session()
			try:
				if selected_single_attribute:
					single_atrib = sesh.query(models.SingleAttributes).filter_by(id=selected_single_attribute).first()
					if svform.mod_delete.data == True:
						sesh.delete(single_atrib)
						sesh.commit()
						flash("Attribute {} Deleted".format(single_atrib.key + ': ' + single_atrib.value))
					else:
						single_atrib.key = svform.mod_key.data
						single_atrib.value = svform.mod_value.data
						sesh.add(single_atrib)
						sesh.commit()
						flash("Attribute Editied")
			except:
				sesh.rollback()
				raise
			finally:
				sesh.close()
		if new_sv_form.key.data:
			sesh = db.session()
			try:
				template = sesh.query(models.UserTemplate).filter_by(id=template_id).first()
				template.add_single_attribute(new_sv_form.key.data, new_sv_form.value.data)
				sesh.add(template)
				sesh.commit()
				flash("Attribute Added")
			except:
				sesh.rollback()
				raise
			finally:
				sesh.close()
		""" Multi Var Logic """
		if mvform.mod_mkey.data or mvform.mod_mdelete.data == True:
			sesh = db.session()
			try:
				if selected_multi_attribute:
					multi_atrib = sesh.query(models.MultiAttributes).filter_by(id=selected_multi_attribute).first()
					if mvform.mod_mdelete.data == True:
						sesh.delete(multi_atrib)
						sesh.commit()
						flash("Attribute {} Deleted".format(multi_atrib.key + ': ' + multi_atrib.value))
					else:
						multi_atrib.key = mvform.mod_mkey.data
						multi_atrib.value = mvform.mod_mvalue.data
						sesh.add(multi_atrib)
						sesh.commit()
						flash("Attribute Editied")
			except:
				sesh.rollback()
				raise
			finally:
				sesh.close()
		if new_mvform.mkey.data:
			sesh = db.session()
			try:
				template = sesh.query(models.UserTemplate).filter_by(id=template_id).first()
				template.add_multi_attribute(new_mvform.mkey.data, new_mvform.mvalue.data)
				sesh.add(template)
				sesh.commit()
				flash("Attribute Added")
			except:
				sesh.rollback()
				raise
			finally:
				sesh.close()
		return (redirect(url_for('admin_org_template', template_id=template_id)))
	if request.method == 'GET':
		if delete == 1:
			sesh = db.session()
			try:
				template = sesh.query(models.UserTemplate).filter_by(id=template_id).first()
				orgid = template.organization
				for sa in template.single_attributes:
					sesh.delete(sa)
				for ma in template.multi_attributes:
					sesh.delete(ma)
				sesh.delete(template)
				sesh.commit()
			except:
				sesh.rollback()
			finally:
				sesh.close()
			return(redirect(url_for('admin_org', admin_org=orgid)))
		sesh = db.session()
		try:
			template = sesh.query(models.UserTemplate).filter_by(id=template_id).first()
			org = sesh.query(models.Organization).filter_by(id=template.organization).first()
			templates = org.templates
			single_attributes = template.single_attributes
			multi_attributes = template.multi_attributes
			""" Get Selected Attribute info to populate form, if selected """
			if selected_single_attribute:
				single_atrib = sesh.query(models.SingleAttributes).filter_by(id=selected_single_attribute).first()
				svform.mod_key.data = single_atrib.key
				svform.mod_value.data = single_atrib.value
			""" Get Selected Multi Attribute to populate form, if selected """
			if selected_multi_attribute:
				multi_atrib = sesh.query(models.MultiAttributes).filter_by(id=selected_multi_attribute).first()
				mvform.mod_mkey.data = multi_atrib.key
				mvform.mod_mvalue.data = multi_atrib.value
		except:
			sesh.rollback()
			raise
		finally:
			sesh.close()
		return render_template(
			'admin_org_template.html',
			form=form,
			svform=svform,
			single_attributes=single_attributes,
			multi_attributes=multi_attributes,
			title='Template Admin: {} ({})'.format(template.name.title(), org.name.title()),
			org=org,
			templates=templates,
			selected_single_attribute=selected_single_attribute,
			selected_multi_attribute=selected_multi_attribute,
			template=template,
			new_sv_form=new_sv_form,
			mvform=mvform,
			version_number=version_number,
			new_mvform=new_mvform
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
						   version_number=version_number,
						   form=form)


@required('Admin')
@login_required
@app.route("/admin/users", methods=['GET', 'POST'])
def admin_users():
	userform = UserCreationForm()
	# Begin GET block
	if request.method == 'GET':
		users = get_users()
		return render_template('admin_users.html',
						userform=userform,
						version_number=version_number,
						users=users)
	# End GET block
	elif request.method == 'POST':
		try:
			create_user(userform.username.data, userform.first_name.data, userform.last_name.data, userform.password.data)
			flash('Created user account for {} {}.'.format(userform.first_name.data, userform.last_name.data))
		except:
			flash('Failed to create user account for {} {}.'.format(userform.first_name.data, userform.last_name.data))
		return redirect(url_for('admin_users'))




@required('Admin')
@login_required
@app.route("/admin/user", methods=['GET', 'POST'])
def admin_user():
	form = AddName()
	user_id = request.args.get('user_id', default=0, type=int)
	delete = request.args.get('delete', default=0, type=int)
	# Begin GET block
	if request.method == 'GET':
		if delete == 1:
			delete_user(user_id)
			return redirect(url_for('admin_users'))
		sesh = db.session()
		try:
			user = sesh.query(models.User).filter_by(id=user_id).first()
			roles = user.roles
		except:
			sesh.rollback()
		finally:
			sesh.close()
		return render_template('admin_user.html',
							   form=form,
							   roles=roles,
							   version_number=version_number,
							   user=user)
	# End GET block
	# Begin POST block
	elif request.method == 'POST':
		rolename = form.name.data
		sesh = db.session()
		try:
			user = sesh.query(models.User).filter_by(id=user_id).first()
			role = sesh.query(models.Role).filter_by(name=rolename).first()
			if not role:
				role = models.Role(rolename)
			user.add_roles(role)
			sesh.add(user)
			sesh.add(role)
			sesh.commit()
			flash('Added role {} to user {} {}'.format(role.name, user.first_name, user.last_name))
			return redirect(url_for('admin_user', user_id=user_id))
		except:
			sesh.rollback()
			flash('Failed to add role {} to user {} {}'.format(role.name, user.first_name, user.last_name))
		finally:
			sesh.close()
	# End POST block

@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for('index'))

