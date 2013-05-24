# -*- coding: utf-8 -*-

from distutils.core import setup

setup(name='tinys3',
      version='0.1.5',
      description=("A small library for uploading files to S3,"
                   "With support of async uploads, worker pools, cache headers etc"),

      author='Shlomi Atar',
      author_email='shlomi@smore.com',
      url='https://github.com/smore-inc/tinys3',
      packages=['tinys3', 'tests'],

      classifiers=[
          # make sure to use :: Python *and* :: Python :: 3 so
          # that pypi can list the package on the python 3 page
          'Programming Language :: Python',
          'Programming Language :: Python :: 3'
      ],

      platforms='Any',
      keywords=('s3', 'upload'),

      package_dir={'': '.'},
      requires=['requests (>= 1.2.0)', 'futures (>= 2.1.3)', 'nose', 'flexmock']
)
