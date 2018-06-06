from app import db, app, models, scheduler
import config
from mldapcommon.ldap_operations import *
from mldapcommon.errors import *
from apscheduler.triggers.interval import IntervalTrigger



def sync_user(ldap, session=None, username='', ldap_guid=None, first_name='', last_name=''):
	user = session.query(models.User).filter_by(ldap_guid=ldap_guid).first()
	if not user:
		app.logger.info("Creating user {}".format(username))
		userobj = models.User(username, first_name=first_name.lower(), last_name=last_name.lower(), ldap_guid=ldap_guid)
		session.add(userobj)
		user = session.query(models.User).filter_by(ldap_guid=ldap_guid).first()
		return user
	else:
		'''Update attributes, if changed'''
		if username != user.username:
			user.username = username
		if first_name != user.first_name:
			user.first_name = first_name
		if last_name != user.last_name:
			user.last_name = last_name
		'''Return the ORM Users object'''
		return user



def sync_roles():
	ldap = LdapOperations(
		config.ldap_server_type,
		server=config.ldap_server,
		domain=config.ldap_domain,
		user=config.ldap_bind_user,
		plaintext_pw=config.ldap_bind_pw
	)

	sesh = db.session()
	app.logger.info("Starting LDAP Sync")
	roles = sesh.query(models.Role).all()
	users = sesh.query(models.User).all()
	for role in roles:
		if role.ldap_group_dn:
			'''Add users to roles they aren't currently a member of'''
			users_to_add = ldap.users_in_group(config.ldap_base_dn, role.ldap_group_dn, attributes=['givenName', 'sn', 'objectGUID', 'sAMAccountName'])
			for user in users_to_add:
				if user.givenName.value:
					firstname = user.givenName.value
				else:
					firstname = ''
				if user.sn.value:
					lastname = user.sn.value
				else:
					lastname = ''
				user_object = sync_user(
					ldap, session=sesh,
					username=user.sAMAccountName.value,
					first_name=firstname,
					last_name=lastname,
					ldap_guid=user.objectGUID.value
				)
				if role not in user_object.roles:
					user_object.add_role(role)
					sesh.add(user_object)
					sesh.add(role)
					sesh.commit()
					app.logger.info("LDAP Sync: Added user {} to role {}".format(user_object.username, role.name))
			'''Remove any users that have been removed from an LDAP group'''
			'''Build list of objectGUIDs that belong in group according to LDAP'''
			users_in_group = []
			for user in users_to_add:
				users_in_group.append(user.objectGUID.value)
			for user in users:
				if user.ldap_guid and user.ldap_guid not in users_in_group:
					if role in user.roles:
						user.roles.remove(role)
						sesh.add(user)
						app.logger.info("LDAP Sync: Removing user {} from role {}".format(user.username, role.name))
	sesh.commit()
	app.logger.info("LDAP Sync complete")

if config.ldap_enabled:
	scheduler.add_job(
		'LDAPSyncJob',
		func=sync_roles,
		trigger=IntervalTrigger(seconds=config.ldap_sync_interval_seconds),
		name='Sync Ldap every {} seconds'.format(config.ldap_sync_interval_seconds),
		replace_existing=True
	)


if __name__ == '__main__':
	sync_roles()