import os
import shutil

from charms.reactive import (
    remove_state,
    set_state,
    when,
    when_any,
    when_not,
)

from charmhelpers.core.hookenv import (
    config,
    open_port,
    resource_get,
    status_set,
    unit_get,
    unit_public_ip,
)

from charmhelpers.core.templating import render
from charmhelpers.payload.archive import extract_tarfile

from charms.layer.nginx import configure_site
from charms.layer.documize import (
    start_restart,
    create_user_and_group_if_not_exists
)


@when_not('documize.installed')
def install_documize_and_user_init():
    """Grab the documize binary, unpack, install
    to /srv, create documize user and group if not exists.
    """

    status_set('maintenance', "Installing Documize")

    create_user_and_group_if_not_exists(user="documize", group="documize")
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
    """Create/request documize database.
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
    """Get/Set mysql connection details once database available.
    """

    documize_systemd_conf = \
        '/etc/systemd/system/documize.service'

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
@when_not('documize.web.available')
def render_nginx_template_restart_nginx():
    """NGINX
    """

    status_set('maintenance', 'Configuring website')
    configure_site('documize', 'documize.nginx.tmpl')
    open_port(config('port'))
    start_restart('nginx')
    status_set('active', 'Documize available: %s' % unit_public_ip())
    set_state('documize.web.available')


@when('documize.web.available')
def set_status_persist():
    """Set status to persist over other layers status.
    """
    status_set('active', 'Documize available: %s' % unit_public_ip())


@when('website.available')
def setup_website(website):
    website.configure(config('port'))


@when('documize.web.available')
@when_any('config.changed.port', 'config.changed.fqdn')
def react_to_fqdn_changed():
    """Re-render nginx template when port or fqdn changes
    """
    remove_state('documize.web.available')
