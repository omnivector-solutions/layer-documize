# Documize

Documize creates the Enterprise Knowledge Backbone by unifying docs, wiki, reporting and dashboards.

composition + coordination + discovery + distribution + workflows = faster business outcomes

[Documize Homepage](https://documize.com/)

# Usage

To deploy Documize, you will need to accompany it with a MySQL database.

Suppored databases:
* [MySQL](https://jujucharms.com/mysql)
* [PerconaDB](https://jujucharms.com/percona-cluster)
* [MariaDB](https://jujucharms.com/mariadb)

We can accomplish this using Juju as follows:
```bash
juju deploy documize

juju deploy mysql

juju relate mysql documize
```


# Authors
* James Beedy <jamesbeedy@gmail.com>

# Copyright
* James Beedy (c) 2017 <jamesbeedy@gmail.com>

# License
* AGPLv3 (see `LICENSE` file)
