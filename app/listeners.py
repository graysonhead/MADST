from sqlalchemy import event
from app.models import *
from app import app


def user_template_change(**kwargs):
    app.logger.info("ORM detected a template modification "
                    "for attribute {}. "
                    "Resyncing users.".format(kwargs['target']))
    print(vars(kwargs['target']))
    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    print(kwargs['initiator'].impl)
    print(kwargs['initiator'].op)
    kwargs['target'].start_sync()


def user_template_append_roles(**kwargs):
    app.logger.info("ORM detected an append action for Role '{}' "
                    "on UserTemplate '{}' for organization '{}'. "
                    "Resyncing users.".format(kwargs['value'],
                                              kwargs['target'],
                                              kwargs['target'].organization))
    kwargs['target'].start_sync()

def user_template_remove_roles(**kwargs):
    app.logger.info("ORM detected an append action for Role '{}' "
                    "on UserTemplate '{}' for organization '{}' "
                    "Resyncing users.".format(kwargs['value'],
                                              kwargs['target'],
                                              kwargs['target'].organization))
    for user in Role.query.get(kwargs['value'].id).users:
        kwargs['target'].add_task(user, task_type='delete')


def organization_modified(target, initiator):
    app.logger.info("ORM detected an organization modification "
                    "update for attribute {}. "
                    "Resyncing organization.".format(target))
    target.start_sync()


def user_disabled(target, value, oldvalue, initiator):
    print("-------------------------------------------user_disabled-------------------------------------------")
    print(target)
    if oldvalue is False and value is True:
        target.start_sync()


def user_name_change(target, value, oldvalue, initiator):
    print("-------------------------------------------user_name_change------------------------------------------")
    print(target)


def single_attribute_update(mapper, connection, target):
    template = UserTemplate.query.get(target.template)
    app.logger.info("ORM detected single variable attribute "
                    "update for attribute {} on template {}, {}. "
                    "Resyncing template.".format(target, template.id, template))
    template.start_sync()


def single_attribute_delete(mapper, connection, target):
    template = UserTemplate.query.get(target.template)
    app.logger.info("ORM detected single variable attribute "
                    "deletion for attribute {} on  template {}, {}. "
                    "Resyncing template.".format(target, template.id, template))
    template.start_sync()


def multi_attribute_update(mapper, connection, target):
    template = UserTemplate.query.get(target.template)
    app.logger.info("ORM detected multi variable attribute "
                    "update for attribute {} on  template {}, {}. "
                    "Resyncing template.".format(target, template.id, template))
    template.start_sync()


def multi_attribute_delete(mapper, connection, target):
    template = UserTemplate.query.get(target.template)
    app.logger.info("ORM detected multi variable attribute "
                    "deletion for attribute {} on  template {}, {}. "
                    "Resyncing template.".format(target, template.id, template))
    template.start_sync()


event.listen(UserTemplate.single_attributes, 'append', user_template_change, named=True)
event.listen(UserTemplate.multi_attributes, 'append', user_template_change, named=True)
event.listen(UserTemplate.roles, 'append', user_template_append_roles, named=True)
event.listen(UserTemplate.roles, 'remove', user_template_remove_roles, named=True)
event.listen(UserTemplate.user_ou, 'modified', user_template_change, named=True)
event.listen(UserTemplate.disabled, 'modified', user_template_change, named=True)
event.listen(Organization.admin_ou, 'modified', organization_modified)
event.listen(Organization.templates, 'modified', organization_modified)
event.listen(Organization.disabled, 'modified', organization_modified)
event.listen(User.disabled, 'set', user_disabled, named=True)
event.listen(User.sync_password, 'modified', organization_modified)
event.listen(User.sync_username, 'set', user_name_change, named=True)
event.listen(SingleAttributes, 'after_delete', single_attribute_delete)
event.listen(SingleAttributes, 'after_update', single_attribute_update)
event.listen(MultiAttributes, 'after_delete', single_attribute_delete)
event.listen(MultiAttributes, 'after_update', single_attribute_update)
