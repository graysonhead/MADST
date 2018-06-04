from app import db, models, app
import config
from mldapcommon.ldap_operations import *
from mldapcommon.errors import *
from app.decorators import with_db_session, ldap_operation



@ldap_operation
def sync_user(ldap, session=None, username='', ldap_guid=None, first_name='', last_name=''):
	user = session.query(models.User).filter_by(ldap_guid=ldap_guid).first()
	if not user:
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


@with_db_session
@ldap_operation
def sync_roles(ldap, sesh):
	roles = sesh.query(models.Role).all()
	users = sesh.query(models.User).all()
	for role in roles:
		if role.ldap_group_dn:
			'''Add users to roles they aren't currently a member of'''
			users_to_add = ldap.users_in_group(config.ldap_base_dn, role.ldap_group_dn, attributes=['givenName', 'sn', 'objectGUID', 'sAMAccountName'])
			for user in users_to_add:
				user_object = sync_user(session=sesh, username=user.sAMAccountName.value, first_name=user.givenName.value, last_name=user.sn.value, ldap_guid=user.objectGUID.value)
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
					user.roles.remove(role)
					sesh.add(user)
					app.logger.info("LDAP Sync: Removing user {} from role {}".format(user.username, role.name))
	sesh.commit()

# scheduler.add_job(
# 	func=sync_roles,
# 	trigger=IntervalTrigger(seconds=config.ldap_sync_interval_seconds),
# 	name='Sync Ldap every {} seconds'.format(config.ldap_sync_interval_seconds),
# 	replace_existing=True
# )