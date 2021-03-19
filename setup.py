import codecs
from setuptools import setup, find_packages
from pathlib2 import Path


def find_files(paths):
    result = []
    basePath = Path('nuxeo-tools-hooks/nxtools/hooks')
    for path in [basePath.glob(path) for path in paths]:
        result += path

    return [str(path.relative_to(basePath)) for path in result if not path.relative_to(basePath).match('tests/**/*')]

setup(
    name='nuxeo-tools-hooks',
    version='1.1.3-dev',
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
    package_data={"nxtools.hooks": find_files(["doc/*", "scripts/*", "**/resources/*"])},
    install_requires=[
        'flask>=0.12.3',
        'Flask-Cors==3.0.2',
        'requests>=2.20.0',
        'requests-oauthlib==0.6.2',
        'PyJWT==1.4.2',
        'cryptography>=2.6.1',
        'PyGithub==1.28',
        'slackclient==1.0.2',
        'jira==1.0.7',
        'jenkinsapi==0.3.3',
        'Jinja2==2.11.3',
        'Unidecode==0.4.19',
        'mongoengine==0.10.6',
        'gevent==1.1.2',
        'geventhttpclient==1.3.1',
        'logmatic-python==0.1.6',
        'paramiko>=2.0.9',
        'lxml==3.7.2',
        'html5lib==0.999999999',
        'CacheControl==0.12.3',
    ]
)
