# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

from distutils.core import setup
from setuptools import find_packages
import os


def local_file(name):
    return os.path.join(os.path.dirname(__file__), name)

SOURCE = local_file("src")
README = local_file("README.rst")


setup(
    name='hecate',
    version="0.1.0",
    author='David R. MacIver',
    author_email='david@drmaciver.com',
    packages=find_packages(SOURCE),
    package_dir={"": SOURCE},
    url='https://github.com/DRMacIver/hecate',
    license='MPL v2',
    description='A selenium style testing library for console applications',
    zip_safe=False,
    long_description=open(README).read(),
    tests_require=['pytest']
)
