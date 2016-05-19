import codecs
from setuptools import setup, find_packages

setup(
    name='nuxeo-tools-hooks',
    version='1.0.0.dev1',
    license='ASL',
    author='Nuxeo',
    author_email='contact@nuxeo.com',
    description='A aggregator for hooks',
    long_description=codecs.open('README.rst', encoding='utf-8').read(),
    url='https://github.com/nuxeo/nuxeo-tools-hooks',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7'
    ],
    keywords='nuxeo',
    packages=find_packages("nuxeo-tools-hooks"),
    package_dir={"nxtools": "nuxeo-tools-hooks/nxtools"},
    package_data={"nxtools.hooks": ["doc/*"]},
    install_requires=[
        'flask',
        'flask-cors',
        'mock',
        'PyGithub',
        'Jinja2',
        'Unidecode',
        'mongoengine',
        'mongomock'
    ]
)
