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
    version='1.1.0.dev0',
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
    package_data={"nxtools.hooks": find_files(["doc/*", "**/resources/*"])},
    install_requires=[
        'Flask==0.11.1',
        'Flask-Cors==2.1.3',
        'requests==2.10.0',
        'requests-oauthlib==0.6.2',
        'PyJWT==1.4.2',
        'cryptography==1.4',
        'PyGithub==1.27.1',
        'jira==1.0.7',
        'Jinja2==2.8',
        'Unidecode==0.4.19',
        'mongoengine==0.10.6',
        'gevent==1.1.2',
        'geventhttpclient==1.3.1'
    ]
)
