from distutils.core import setup

setup(name='tinys3',
      version='0.1',
      description=("A small library for uploading files to s3,"
                   "With support of async uploads, worker pools, cache headers etc"),

      author='Shlomi Atar',
      author_email='shlomi@smore.com',
      url='https://github.com/smore-inc/tinys3',
      packages=['tinys3', 'tests'],

      platforms='Any',
      keywords=('s3', 'upload', 'workerpool'),

      package_dir={'': '.'},
      requires=['requests (>= 1.1.0)', 'workerpool (>= 0.9.2)', 'nose', 'flexmock']
)
