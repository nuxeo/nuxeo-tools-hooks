========================
Nuxeo Tools Captain Hook
========================

.. image:: https://qa.nuxeo.org/jenkins/buildStatus/icon?job=/Misc/nuxeo-tools-hooks-branches/master
         :target: https://qa.nuxeo.org/jenkins/job/Misc/job/nuxeo-tools-hooks-branches/job/master/

About
=====

* Captain Hook is meant to be the target of any webhook that should trigger an action
* Project status: working

Installation
============

- Clone project
- (Optional) Create a Python virtalenv
- Install requirements with pip install -r dev-requirements.txt
- Add nuxeo-tools-hooks to your PYTHONPATH
- Run with python nuxeo-tools-hooks/nxtools/hooks/app.py

Usage
=====

Please read https://wiki.nuxeo.com/display/NIG/Captain+Hooks

********
Features
********

- Complete & accessible JSON-based API

Code
====

*****
Build
*****

    python setup.py sdist

******
Deploy
******


- Copy dist/nuxeo-tools-hooks-\*.tar.gz on the target server
- Run pip install /path/to/nuxeo-tools-hooks-\*.tar.gz

*******************************
Contributing & Reporting issues
*******************************

Nuxeo Tools Captain Hook is written and maintained by `Nuxeo <contact@nuxeo.com>`_.

`See here for the full list of contributors <https://github.com/nuxeo/nuxeo-tools-hooks/graphs/contributors>`_.

https://jira.nuxeo.com/browse/NXBT/component/14708/

License
=======

`Apache License, Version 2.0 <http://www.apache.org/licenses/LICENSE-2.0.html>`_

About Nuxeo
===========

The `Nuxeo Platform <http://www.nuxeo.com/products/content-management-platform/>`_ is an open source customizable and extensible content management platform for building business applications. It provides the foundation for developing `document management <http://www.nuxeo.com/solutions/document-management/>`_, `digital asset management <http://www.nuxeo.com/solutions/digital-asset-management/>`_, `case management application <http://www.nuxeo.com/solutions/case-management/>`_ and `knowledge management  <http://www.nuxeo.com/solutions/advanced-knowledge-base/>`_. You can easily add features using ready-to-use addons or by extending the platform using its extension point system.

The Nuxeo Platform is developed and supported by Nuxeo, with contributions from the community.

Nuxeo dramatically improves how content-based applications are built, managed and deployed, making customers more agile, innovative and successful. Nuxeo provides a next generation, enterprise ready platform for building traditional and cutting-edge content oriented applications. Combining a powerful application development environment with
SaaS-based tools and a modular architecture, the Nuxeo Platform and Products provide clear business value to some of the most recognizable brands including Verizon, Electronic Arts, Sharp, FICO, the U.S. Navy, and Boeing. Nuxeo is headquartered in New York and Paris.
More information is available at `www.nuxeo.com <http://www.nuxeo.com>`_.
