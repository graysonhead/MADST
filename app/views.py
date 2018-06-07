from flask import render_template, flash, redirect, url_for, request
import config
from werkzeug.exceptions import Forbidden
from app import app, db, models, g, login_manager, login_user, logout_user, login_required, current_user, version_number
from app.sync import sync_roles, sync_user
from .decorators import required, with_db_session, no_disabled_users, ldap_operation
from mldapcommon.ldap_operations import LdapServerType, LdapOperations
from mldapcommon.errors import *
from .forms import \
	LoginForm, \
	PasswordChange, \
	AddName, \
	KeyValueAdd, \
	KeyValueModify, \
	MultiKeyValueAdd, \
	MultiKeyValueModify, \
	UserCreationForm, \
	AddAdminUser, \
	OUName, \
	AddRole, \
	NewRole, \
	BillingGroup, \
	DNName

# from flask.ext.permissions.decorators import user_is, user_has

def get_current_role_ids(session, template_id):
	template = session.query(models.UserTemplate).filter_by(id=template_id).first()
	roleids = []
	for r in template.roles:
		roleids.append(r.id)
	return roleids

def get_template(session, id):
	return session.query(models.UserTemplate).filter_by(id=id).first()

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

def get_role(session, id):
	return session.query(models.Role).filter_by(id=id).first()

def create_user(session, username, first_name, last_name, password):
	user = models.User(username, first_name.lower(), last_name.lower(), password=password)
	session.add(user)
	session.commit()

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



def delete_current_tasks(sesh, user):
	for i in user.get_current_tasks():
		sesh.delete(i)
	sesh.commit()




@ldap_operation
def search_ldap(
		ldap_connection, basedn=None, username=None, attributes=['userPrincipalName', 'sAMAccountName']):
	return ldap_connection.find_dn_from_username(basedn, username, attributes)

@ldap_operation
def login_from_dn(ldap_connection, db_session, dn):
	ldap_connection.conn.search(config.ldap_base_dn, '(distinguishedName={})'.format(dn), attributes='objectGuid')
	return db_session.query(models.User).filter_by(ldap_guid=ldap_connection.conn.entries[0].objectGUID.value).first()

def check_credentials(server=config.ldap_server, domain=config.ldap_domain, user=None, plaintext_pw=None):
	ldap = LdapOperations(config.ldap_server_type, server=server, domain=domain, user=user, plaintext_pw=plaintext_pw)


def log_pageview(request):
	app.logger.info("Someone viewed %s" % request)


@login_manager.user_loader
def load_user(username):
	return db.session.query(models.User).filter_by(username=username).first()


@app.before_request
def before_request():
	g.user = current_user

@app.route('/admin/orgs', methods=['GET', 'POST'])
@login_required
@required('admin')
@no_disabled_users
@with_db_session
def admin_orgs(sesh):
	""" Displays list of organizations and allows you to navigate to their respective admin pages"""
	form = AddName()
	if request.method == 'POST':
		name = form.name.data
		org = models.Organization(name)
		sesh.add(org)
		sesh.commit()
		flash('Added new organization {}.'.format(name))
		return (redirect(url_for('admin_orgs')))
	if request.method == 'GET':
		orgs = []
		for o in sesh.query(models.Organization).all():
			if not o.disabled:
				orgs.append(o)
		return render_template(
			'admin_orgs.html',
			title='Organization Admin',
			form=form,
			version_number=version_number,
			orgs=orgs
		)

@app.route('/index', methods=['GET', 'POST'])
@login_required
@required('technician')
@no_disabled_users
@with_db_session
def index(sesh):
	form = PasswordChange()
	if form.password.data:
		if form.password.data == form.password_confirm.data:
			password = form.password.data
			user = sesh.query(models.User).filter_by(id=g.user.id).first()
			delete_current_tasks(sesh, user)
			user.set_sync_password(password)
			sesh.add(user)
			app.logger.info("{} changed their sync password".format(g.user.username))
			sesh.commit()
			flash("Sync password changed.")
		else:
			flash("Passwords did not match.")
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

@app.route('/admin', methods=['GET'])
@login_required
@required('admin')
@no_disabled_users
def admin():
	return render_template(
		'admin.html',
		version_number=version_number,
		title='Admin'
	)

@app.route('/admin/org', methods=['GET', 'POST'])
@login_required
@required('admin')
@no_disabled_users
@with_db_session
def admin_org(sesh):
	""" Allows viewing and modification of Organization Attributes"""
	org_id = request.args.get('org_id', default=1, type=int)
	delete = request.args.get('delete', default=0, type=int)
	resync = request.args.get('resync', default=0, type=int)
	form = AddName()
	userform = AddAdminUser()
	billinggroupform = BillingGroup()
	org = sesh.query(models.Organization).filter_by(id=org_id).first()
	# Begin POST block
	if request.method == 'POST':
		if form.name.data:
			org = sesh.query(models.Organization).filter_by(id=org_id).first()
			org.add_template(form.name.data)
			sesh.add(org)
			sesh.commit()
			flash("Added {} to {}".format(form.name.data, org.name))
		elif userform.adminname.data:
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
		elif billinggroupform.group.data:
			org.billing_group = billinggroupform.group.data
			sesh.add(org)
			sesh.commit()
			flash("Changed billing OU for org {} to {}".format(org.name, billinggroupform.group.data))
		return(redirect(url_for("admin_org", org_id = org_id)))
	# End POST block
	# Begin GET block
	if request.method == 'GET':
		billinggroupform.group.data = org.billing_group
		if delete == 1:
			org.disabled = True
			sesh.add(org)
			sesh.commit()
			flash("Deleted organization {}.".format(org.name))
			return(redirect(url_for('admin_orgs')))
		elif resync == 1:
			org = sesh.query(models.Organization).filter_by(id=org_id).first()
			for t in org.templates:
				for r in t.roles:
					for u in r.users:
						if u.sync_password is not None:
							delete_current_tasks(sesh, u)
							t.add_task(u)
			flash("Created sync tasks for all admin users in organization {}".format(org.name))
			sesh.commit()
			return(redirect(url_for('admin_org', org_id=org_id)))

		org = sesh.query(models.Organization).filter_by(id=org_id).first()
		templates = []
		for t in org.templates:
			if not t.disabled:
				templates.append(t)
		admin_users = org.admin_users
		return render_template(
			'admin_org.html',
			form=form,
			userform=userform,
			title='Organization Admin: {}'.format(org.name.title()),
			org=org,
			admin_users=admin_users,
			version_number=version_number,
			templates=templates,
			billinggroupform=billinggroupform
		)
	#End GET block

@app.route('/admin/org/template', methods=['GET', 'POST'])
@login_required
@required('admin')
@no_disabled_users
@with_db_session
def admin_org_template(sesh, **kwargs):
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
	ouform = OUName()
	roleform = AddRole()
    # Begin POST block
	if request.method == 'POST':
		template_id = request.args.get('template_id', default=1, type=int)
		""" Stuff Every request needs """
		template = sesh.query(models.UserTemplate).filter_by(id=template_id).first()
		""" Single Value Logic """
		if request.form.getlist('remove_role'):
				role_id = request.form['remove_role']
				role = get_role(sesh, role_id)
				template.roles.remove(role)
				sesh.commit()
				flash("Removed role {} from template {}".format(role.name, template.name))
		elif svform.mod_key.data or svform.mod_delete.data == True:
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
		elif new_sv_form.key.data:
			template = sesh.query(models.UserTemplate).filter_by(id=template_id).first()
			template.add_single_attribute(new_sv_form.key.data, new_sv_form.value.data)
			sesh.add(template)
			sesh.commit()
			flash("Attribute Added")
		""" Multi Var Logic """
		if mvform.mod_mkey.data or mvform.mod_mdelete.data == True:
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
		elif new_mvform.mkey.data:
			template = sesh.query(models.UserTemplate).filter_by(id=template_id).first()
			template.add_multi_attribute(new_mvform.mkey.data, new_mvform.mvalue.data)
			sesh.add(template)
			sesh.commit()
			flash("Attribute Added")
		elif ouform.ouname.data:
			template = sesh.query(models.UserTemplate).filter_by(id=template_id).first()
			template.user_ou = ouform.ouname.data
			sesh.add(template)
			sesh.commit()
			flash("OU DN changed")
		elif not roleform.rolename.data == roleform.rolename.default:
			role = sesh.query(models.Role).filter_by(id=roleform.rolename.data).first()
			template.add_role(role)
			sesh.add(role)
			sesh.commit()
			flash("Added role {} to template {}.".format(role.name, template.name))
		# After we are done submitting values, redirect to the page we submitted from
		return (redirect(url_for('admin_org_template', template_id=template_id)))
	# End POST block
	# Begin GET block
	if request.method == 'GET':
		template = sesh.query(models.UserTemplate).filter_by(id=template_id).first()
			# Logic to populate Roles drop down
		roles = sesh.query(models.Role).all()
		choices = [(0, "Select Template")]
		for r in roles:
			if r.id not in get_current_role_ids(sesh, template_id):
				choices.append((r.id, r.name))
			roleform.rolename.choices = choices
		if delete == 1:
			template = sesh.query(models.UserTemplate).filter_by(id=template_id).first()
			template.disabled = True
			sesh.add(template)
			sesh.commit()
			return(redirect(url_for('admin_org', admin_org=template.organization.id)))
		template = sesh.query(models.UserTemplate).filter_by(id=template_id).first()
		org = template.organization
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
		# Set Template OU DN data form equal to current value
		ouform.ouname.data = template.user_ou
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
			new_mvform=new_mvform,
			ouform=ouform,
			roleform=roleform
		)


@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if request.method == 'POST':
		if g.user is not None and g.user.is_authenticated:
			return redirect(url_for('index'))
		if form:
			username = form.username.data
			password = form.password.data
			remember_me = form.remember_me.data
			try:
				userObj = db.session.query(models.User).filter_by(username=username).first()
				passval = userObj.check_password(password)
				if passval:
					app.logger.info("User %s logged in" % userObj.username)
					login_user(userObj, remember=remember_me)
					g.current_user = userObj
					flash('You have logged in successfully')
					return redirect(url_for('index'))
			except AttributeError:
				''' If LDAP auth is enabled, check the directory '''
				try:
					dn = search_ldap(basedn=config.ldap_base_dn, username=username)
					if dn:
						sesh = db.session()
						check_credentials(user=dn, plaintext_pw=password)
						try:
							#TODO: We shouldn't be calling Sync here, another function proably needs to be created to sync a single user, but this works for now
							sync_roles()
							user_object = login_from_dn(sesh, dn)
							login_user(user_object)
						except AttributeError:
							flash("You entered correct LDAP credentials, "
							      "but this user is not authorized to access any pages. "
							      "Check your LDAP group membership and MADST configuration.")
							return render_template('login.html',
							                       title='Sign In',
							                       version_number=version_number,
							                       form=form)
						g.current_user = user_object
						flash("Directory Login successful.")
						return redirect(url_for('index'))
				except LdapBindError:
						flash("Incorrect username or password.")
						app.logger.info("User {} attempted domain login with incorrect information."
						                .format(username))
				except LdapConnectError:
					flash("The Directory server failed to respond, please contact your administrator.")
					app.logger.info("User {} loookup on directory server {} failed."
					                .format(username, config.ldap_server)
					                )
			flash("Account information not found or password incorrect.")
			return render_template('login.html',
		                       title='Sign In',
		                       version_number=version_number,
		                       form=form)
			# app.logger.info('User {0} attempted to login with incorrect password'.format(form.username.data))
			# flash("Incorrect password")


		else:
			app.logger.info('User attempted to login with unknown username {0}'.format(form.username.data))

	elif request.method == 'GET':
		return render_template('login.html',
							   title='Sign In',
							   version_number=version_number,
							   form=form)


@app.route("/admin/users", methods=['GET', 'POST'])
@login_required
@required('admin')
@no_disabled_users
@with_db_session
def admin_users(sesh):
	userform = UserCreationForm()
	# Begin GET block
	if request.method == 'GET':
		users = get_users()
		return render_template('admin_users.html',
						userform=userform,
						version_number=version_number,
						users=users
		                       )
	# End GET block
	elif request.method == 'POST':
		try:
			create_user(sesh, userform.username.data, userform.first_name.data, userform.last_name.data, password=userform.password.data)
			flash('Created user account for {} {}.'.format(userform.first_name.data, userform.last_name.data))
		except:
			flash('Failed to create user account for {} {}.'.format(userform.first_name.data, userform.last_name.data))
		return redirect(url_for('admin_users'))



@app.route("/admin/user", methods=['GET', 'POST'])
@login_required
@required('admin')
@no_disabled_users
@with_db_session
def admin_user(sesh):
	form = AddName()
	roleform = AddRole()
	user_id = request.args.get('user_id', default=0, type=int)
	delete = request.args.get('delete', default=0, type=int)
	disable = request.args.get('disable', default=0, type=int)
	enable = request.args.get('enable', default=0, type=int)
	user = sesh.query(models.User).filter_by(id=user_id).first()
	# Begin POST block
	if request.method == 'POST':
		if not roleform.rolename.data == roleform.rolename.default:
			role = sesh.query(models.Role).filter_by(id=roleform.rolename.data).first()
			user.add_role(role)
			sesh.add(role)
			sesh.add(user)
			sesh.commit()
			flash("Role {} added to user {}".format(role.name, user.first_name.title() + ' ' + user.last_name.title()))
		elif request.form.getlist('remove_role'):
			role_id = request.form['remove_role']
			role = get_role(sesh, role_id)
			if role.name == 'admin' and len(role.users) == 1:
				flash("You can't remove the last user from the admin group, or you won't be able to add any more users.")
			elif user_id == current_user.id:
				flash("You can't remove yourself from the admin group, another admin has to do that.")
			else:
				user.roles.remove(role)
				sesh.add(user)
				sesh.commit()
				flash("Removed role {} from user {}.".format(role.name, user.first_name.title() + ' ' + user.last_name.title()))
		return redirect(url_for('admin_user', user_id=user_id))
	# End POST block
	# Begin GET block

	elif request.method == 'GET':
		# Build role selector
		roles = sesh.query(models.Role).all()
		choices = [(0, "Select Template")]
		for r in roles:
			if r not in user.roles:
				choices.append((r.id, r.name))
		roleform.rolename.choices = choices
		if delete == 1:
			if user.check_role('admin'):
				flash("You cannot delete admin users without first removing them from the admin group.")
			else:
				delete_user(user_id)
				return redirect(url_for('admin_users'))
		if disable == 1:
			if user.check_role('admin'):
				flash("You cannot disable admin users without first removing them from the admin group.")
			else:
				user.disable()
				sesh.add(user)
				sesh.commit()
		elif enable == 1:
			user.enable()
			sesh.add(user)
			sesh.commit()
		roles = user.roles
		return render_template('admin_user.html',
							   form=form,
							   roles=roles,
							   roleform=roleform,
							   version_number=version_number,
							   user=user)
	# End GET block


@app.route("/admin/roles", methods=['GET', 'POST'])
@login_required
@required('admin')
@no_disabled_users
@with_db_session
def admin_roles(sesh):
	selected_role = request.args.get('selected_role', default=0, type=int)
	""" Forms """
	newrole = NewRole()
	dnform = DNName()
	# Begin POST block
	if request.method == 'POST':
		if request.form.getlist('delete_role'):
			role_id = request.form['delete_role']
			role = get_role(sesh, role_id)
			role.disabled = True
			sesh.add(role)
			sesh.commit()
			flash("Deleted role {}".format(role.name))
		elif dnform.dnname.data:
			role = sesh.query(models.Role).filter_by(id=selected_role).first()
			role.ldap_group_dn = dnform.dnname.data
			sesh.add(role)
			sesh.commit()
			flash("Role {} ldap DN changed to {}".format(role.name, role.ldap_group_dn))
		elif newrole.newrole.data:
			role = models.Role(newrole.newrole.data)
			if newrole.ldap_dn.data:
				role.ldap_group_dn = newrole.ldap_dn.data
			sesh.add(role)
			sesh.commit()
			flash("Added role {}".format(role.name))
		return redirect(url_for('admin_roles'))
	# End POST block
	# Begin GET block
	if request.method == 'GET':
		roles = []
		for r in sesh.query(models.Role).all():
			if not r.disabled:
				roles.append(r)
		if selected_role:
			selected_role_data = sesh.query(models.Role).filter_by(id=selected_role).first()
			dnform.dnname.data = selected_role_data.ldap_group_dn
		return render_template('admin_roles.html',
		                       selected_role=selected_role,
		                       roles=roles,
							   newrole=newrole,
		                       dnform=dnform,
							   version_number=version_number)
	#End GET block

@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for('index'))

