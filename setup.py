#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Monk is a lightweight schema/query framework for document databases.
#    Copyright © 2011  Andrey Mikhaylenko
#
#    This file is part of Monk.
#
#    Monk is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Monk is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with Monk.  If not, see <http://gnu.org/licenses/>.
#
import os
from setuptools import setup

import monk


readme = open(os.path.join(os.path.dirname(__file__), 'README')).read()

setup(
    # overview
    name             = 'monk',
    description      = 'A lightweight schema/query framework for MongoDB',
    long_description = readme,

    # technical info
    version  = monk.__version__,
    packages = ['monk'],
    requires = ['python (>= 2.7)'],
    provides = ['monk'],

    # copyright
    author   = 'Andrey Mikhaylenko',
    author_email = 'neithere@gmail.com',
    license  = 'GNU Lesser General Public License (LGPL), Version 3',

    # more info
    url          = 'http://bitbucket.org/neithere/monk/',
    download_url = 'http://bitbucket.org/neithere/monk/get/tip.zip',

    # categorization
    keywords     = ('mongo mongodb document query database api model models '
                    'orm odm document-oriented non-relational nosql '
                    'validation'),
    classifiers  = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Programming Language :: Python',
        'Topic :: Database :: Front-Ends',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    # release sanity check
    test_suite = 'nose.collector',
)
