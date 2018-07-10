from app import db, app, models, scheduler
from app.models import User
import config
from mldapcommon.ldap_operations import *
from mldapcommon.errors import *
from apscheduler.triggers.interval import IntervalTrigger



def sync_user(ldap_user, session):
	"""

	:param session: sqlalchemy db session
	:param ldap_user: ldap3 User object
	:return:
	"""

	username = ldap_user.sAMAccountName.value
	ldap_guid = ldap_user.objectGUID.value
	if ldap_user.givenName.value:
		first_name = ldap_user.givenName.value
	else:
		first_name = ''
	if ldap_user.sn.value:
		last_name = ldap_user.sn.value
	else:
		last_name = ''

	user = session.query(models.User).filter_by(ldap_guid=ldap_user.objectGUID.value).first()
	disabled_account_values = [
		514,
		546,
		66050,
		66082,
		262658,
		262690,
		328194,
		328226
	]
	if ldap_user.userAccountControl.value not in  disabled_account_values:
		if not user:
			app.logger.info("Creating user {}".format(username))
			user = models.User(username, first_name=first_name.lower(), last_name=last_name.lower(), ldap_guid=ldap_guid)
			session.add(user)
		else:
			'''Update attributes, if changed'''
			if username != user.username:
				user.username = username
			if first_name != user.first_name:
				user.first_name = first_name
			if last_name != user.last_name:
				user.last_name = last_name
			'''Return the ORM Users object'''
			session.add(user)
	else:
		if user:
			session.delete(user)
			app.logger.info("LDAP user disabled. Deleting user {}.".format(username))
			user = None

	return user

def sync_roles():
	with app.app_context():
		ldap = LdapOperations(
			config.ldap_server_type,
			server=config.ldap_server,
			domain=config.ldap_domain,
			user=config.ldap_bind_user,
			plaintext_pw=config.ldap_bind_pw
		)

		sesh = db.session(autoflush=False)
		app.logger.info("Starting LDAP Sync")
		roles = sesh.query(models.Role).all()
		users = sesh.query(models.User).all()
		for role in roles:
			if role.ldap_group_dn:
				'''Add users to roles they aren't currently a member of'''
				ldap_users = ldap.users_in_group(config.ldap_base_dn, role.ldap_group_dn, attributes=['givenName', 'sn', 'objectGUID', 'sAMAccountName', 'userAccountControl'])
				for ldap_user in ldap_users:
					user_object = sync_user(ldap_user, sesh)
					if user_object and role not in user_object.roles:
						user_object.add_role(role)
						sesh.add(user_object)
						sesh.add(role)
						app.logger.info("LDAP Sync: Added user {} to role {}".format(user_object.username, role.name))
				'''Remove any users that have been removed from an LDAP group'''
				'''Build list of objectGUIDs that belong in group according to LDAP'''
				users_in_group = []
				for user in ldap_users:
					users_in_group.append(user.objectGUID.value)
				for user in users:
					if user.ldap_guid and user.ldap_guid not in users_in_group:
						if role in user.roles:
							user.roles.remove(role)
							sesh.add(user)
							app.logger.info("LDAP Sync: Removing user {} from role {}".format(user.username, role.name))
		sesh.commit()
		sesh.close()
		app.logger.info("LDAP Sync complete")

if config.ldap_enabled:
	scheduler.add_job(
		'LDAPSyncJob',
		func=sync_roles,
		trigger=IntervalTrigger(seconds=config.ldap_sync_interval_seconds),
		name='Sync Ldap every {} seconds'.format(config.ldap_sync_interval_seconds),
		replace_existing=True,
		max_instances = 1
	)
	app.logger.info("Scheduler Jobs: {}".format(scheduler.get_jobs()))


if __name__ == '__main__':
	sync_roles()