#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name='earwig',
      version='0.1',
      packages=find_packages(),
      author='James Turk',
      author_email='jturk@sunlightfoundation.com',
      license='BSD',
      url='http://github.com/sunlightlabs/earwig/',
      description='contact tool',
      long_description='',
      platforms=['any'],
      install_requires=[
          'Django>1.6',
          'pytz',
      ]
)
