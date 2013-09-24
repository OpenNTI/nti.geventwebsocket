#!/usr/bin/env python
from setuptools import setup, find_packages
import codecs

VERSION = '0.0.1'

entry_points = {

}

setup(
    name = 'nti.geventwebsocket',
    version = VERSION,
    author = 'Jason Madden',
    author_email = 'open-source@nextthought.com',
    description = ('Gevent and gunicorn compatible websockets'),
    long_description = codecs.open('README.rst', encoding='utf-8').read(),
    license = 'Apache',
    keywords = 'nose exceptions zope',
    url = 'https://github.com/NextThought/nti.geventwebsocket',
    classifiers = [
		'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
		'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
		'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Testing'
        ],
	packages=find_packages('src'),
	package_dir={'': 'src'},
	install_requires=[
		'setuptools',
		'gevent',
		'greenlet',
		'zope.interface'
	],
	setup_requires = [
		# Without this, we don't get data files in sdist,
		# which in turn means tox can't work
		'setuptools-git'
	],
#	namespace_packages=['nti'],
	entry_points=entry_points
)
