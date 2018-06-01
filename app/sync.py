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
	for role in roles:
		print(role)
		if role.ldap_group_dn:
			add_users = ldap.users_in_group(config.ldap_base_dn, role.ldap_group_dn, attributes=['givenName', 'sn', 'objectGUID', 'sAMAccountName'])
			for user in add_users:
				user_object = sync_user(session=sesh, username=user.sAMAccountName.value, first_name=user.givenName.value, last_name=user.sn.value, ldap_guid=user.objectGUID.value)
				user_object.add_role(role)
				sesh.add(user_object)
				sesh.add(role)
				sesh.commit()
				app.logger.info("LDAP Sync: Added user {} to role {}".format(user_object.username, role.name))
