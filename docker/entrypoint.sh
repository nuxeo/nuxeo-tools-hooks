#!/bin/bash -ex

pip install --upgrade /opt/dist/nuxeo-tools-hooks-*.tar.gz

# Apache gets grumpy about PID files pre-existing
rm -f /var/run/apache2/apache2.pid
rm -f /var/run/apache2/wsgi*.sock

/usr/sbin/apache2ctl -D FOREGROUND
