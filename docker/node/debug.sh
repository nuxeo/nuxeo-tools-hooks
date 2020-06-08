#!/bin/bash -ex

pip uninstall -y nuxeo-tools-hooks
pip install -r /opt/dev-requirements.txt
pip install -e /opt

cat <<EOF | python

import pydevd
from nxtools.hooks.app import application

pydevd.settrace('172.20.0.1', port=41105, stdoutToServer=True, stderrToServer=True, patch_multiprocessing=True, suspend=False)
application.run()

EOF