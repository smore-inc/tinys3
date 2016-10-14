# -*- coding: utf-8 -*-
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

install_requires = ['requests >= 1.2.0']
if sys.version_info < (3, 2):
    install_requires.insert(0, 'futures >= 2.1.3')

setup(name='tinys3',
      version='0.1.12',
      description=("A small library for uploading files to S3,"
                   "With support of async uploads, worker pools, cache headers etc"),

      author='Shlomi Atar',
      author_email='shlomi@smore.com',
      url='https://www.smore.com/labs/tinys3/',
      packages=['tinys3'],
      license='MIT', 

      classifiers=[
          # make sure to use :: Python *and* :: Python :: 3 so
          # that pypi can list the package on the python 3 page
          'Programming Language :: Python',
          'Programming Language :: Python :: 3'
      ],

      platforms='Any',
      keywords=('amazon', 'aws', 's3', 'upload'),

      package_dir={'': '.'},
      install_requires=install_requires,
      tests_require=['nose', 'flexmock'],
      test_suite='tinys3.tests'
)
