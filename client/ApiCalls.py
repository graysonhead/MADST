from decorators import *
from config import Config

config = Config()

@ApiAuth
def get_count_dn():
    r = requests.get(
        config.host + 'api/org/users/count',
        params={
            'apikey': config.apikey,
            'secret': config.private_key,
            'org_id': config.org_id
        }
    )
    return r

@ApiAuth
def update_count(count):
    r = requests.put(
        config.host + 'api/org/users/count',
        params={
            'apikey': config.apikey,
            'secret': config.private_key,
            'org_id': config.org_id
        },
        json={'billable_users': count}
    )
    return r

@ApiAuth
def task_check():
    params = {
        'apikey': config.apikey,
        'secret': config.private_key,
        'org_id': config.org_id
    }
    return requests.get(
        config.host + 'api/tasks',
        params=params
    )

#@ApiAuth
def change_task_status(task_id, status_id):
    requests.put(
        config.host + 'api/task/' + str(task_id),
        params={
            'apikey': config.apikey,
            'secret': config.private_key
        },
        json={'status': status_id}
    )
