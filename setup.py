#!/usr/bin/env python
import codecs
from setuptools import setup, find_packages

import platform
py_impl = getattr(platform, 'python_implementation', lambda: None)
IS_PYPY = py_impl() == 'PyPy'

VERSION = '0.1'

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
		'zope.interface',
		'gevent' if not IS_PYPY else '',
		'greenlet' if not IS_PYPY else ''
	],
	setup_requires = [
		# Without this, we don't get data files in sdist,
		# which in turn means tox can't work
		'setuptools-git'
	],
	entry_points=entry_points
)
