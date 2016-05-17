#!/bin/bash -ex

pip install --upgrade /opt/dist/nuxeo-tools-hooks-*.tar.gz

ln -nsf /usr/local/lib/python2.7/dist-packages/nxtools/hooks/doc/vhost.conf /etc/apache2/sites-enabled/

/usr/sbin/apache2ctl -D FOREGROUND