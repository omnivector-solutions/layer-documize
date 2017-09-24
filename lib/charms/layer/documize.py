from charmhelpers.core.host import (
    add_group,
    adduser,
    user_exists,
    group_exists,
    service_running,
    service_start,
    service_restart
)


def create_user_and_group_if_not_exists(user, group):
    """Create documize user & group if not exists
    """
    if not group_exists(group):
        add_group(group)
    if not user_exists(user):
        adduser(user, system_user=True)


def start_restart(service):
    if not service_running(service):
        service_start(service)
    else:
        service_restart(service)
