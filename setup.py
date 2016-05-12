import codecs
from setuptools import setup

setup(
    name='nuxeo-tools-notify-center',
    version='1.0.0.dev1',
    license='ASLREADME.rst',
    author='Nuxeo',
    author_email='contact@nuxeo.com',
    description='A simple notification aggregator',
    long_description=codecs.open('README.rst', encoding='utf-8').read(),
    url='https://github.com/nuxeo-sandbox/nuxeo-tools-notify-center',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: System :: Networking',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7'
    ],
    keywords='nuxeo',
    install_requires=[
        'mock',
        'PyGithub',
        'Jinja2',
        'Unidecode',
        'mongoengine',
        'mongomock'
    ]
)