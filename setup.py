from setuptools import setup, find_packages
import sys, os

version = "0.1.1"

long_description = open('README.txt').read()
changes = open('changes.txt').read()

long_description = """%s

New in this version:

%s""" % (long_description, changes)

setup(name='svenweb',
      version=version,
      description="web frontend to versioncontrolled document repository for read-write-index-history operations",
      long_description=long_description,
      classifiers=[], # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      author='Ethan Jucovy and Jeff Hammel',
      author_email='ejucovy@gmail.com',
      url='',
      license="GPLv3 or later",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
         'WebOb',
         'Paste',
         'PasteScript',
         'Tempita',
         'simplejson',
         'sven',
      ],

      entry_points="""
      # -*- Entry points: -*-
      [paste.app_factory]
      main = svenweb.factory:factory
      """,
      )
      
