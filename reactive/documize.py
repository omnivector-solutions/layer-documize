import os
import socket
import shutil

from charms.reactive import (
    hook,
    when,
    when_not,
    set_state,
    remove_state
)

from charmhelpers.core.hookenv import (
    status_set,
    unit_get,
    close_port,
    open_port,
    unit_public_ip,
    unit_private_ip,
    resource_get,
    config,
    local_unit
)

from charmhelpers.core.host import (
    add_group,
    adduser,
    user_exists,
    group_exists,
    service_running,
    service_start,
    service_restart
)

from charmhelpers.core.templating import render
from charmhelpers.payload.archive import extract_tarfile

from charms.layer.nginx import configure_site
from charms.layer import options


@when_not('documize.installed')
def install_documize():
    """Grab the documize binary, unpack, install
    to /srv.
    """

    status_set('maintenance', "Installing Documize")

    # Create documize user & group if not exists
    if not group_exists('documize'):
        add_group("documize")
    if not user_exists('documize'):
        adduser("documize", system_user=True)

    # Get and uppack resource
    if os.path.exists('/srv/documize'):
        shutil.rmtree('/srv/documize')

    documize_bdist = resource_get('bdist')
    extract_tarfile(documize_bdist, destpath="/srv")

    set_state('documize.installed')
    status_set('active', 'Documize installation complete')


@when('database.connected')
@when_not('documize.db.created')
def create_db(database):
    """Create db
    """

    status_set("maintenance", "Creating MySQL database")

    # Get unit ip
    host = unit_get('private-address')
    # Create documize db
    database.configure('documize', 'documize', host, prefix="documize")
    # Set active status
    status_set("active", "Documize db created")
    # Set state
    set_state('documize.db.created')


@when('database.available', 'documize.installed')
@when_not('documize.systemd.available')
def get_set_db_conn(database):
    """Get/Set mysql connection details
    """

    documize_systemd_conf = '/etc/systemd/system/documize.service'

    # Check for and render systemd template
    if os.path.exists(documize_systemd_conf):
        os.remove(documize_systemd_conf)

    render(source="documize.service.tmpl",
           target=documize_systemd_conf,
           perms=0o644,
           owner="root",
           context={'host': database.db_host(),
                    'user': database.username("documize"),
                    'pass': database.password("documize")})
    set_state('documize.systemd.available')


@when('nginx.available', 'documize.systemd.available')
@when_not('documize.web.configured')
def configure_webserver():
    """Configure nginx
    """

    status_set('maintenance', 'Configuring website')
    configure_site('documize', 'documize.nginx.tmpl')
    open_port(config('port'))
    restart_service()
    status_set('active', 'Documize available: %s' % unit_public_ip())
    set_state('documize.web.configured')


@when('documize.web.configured')
def set_status_persist():
    """Set status to persist over other layers status
    """
    status_set('active', 'Documize available: %s' % unit_public_ip())


def restart_service():
    if service_running("documize"):
        service_restart("documize")
    else:
        service_start("documize")


@when('website.available')
def setup_website(website):
    website.configure(config('port'))


@when('config.changed.port')
def react_to_fqdn_changed():
    """Re-render nginx template
    """
    remove_state('documize.web.configured')
