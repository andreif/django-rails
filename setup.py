# coding=utf-8
from setuptools import setup, find_packages

setup(name='rails',
      version='0.0a',
      download_url='git@github.com:andreif/django-rails.git',
      packages=find_packages(exclude=['_*']),
      author='Andrei Fokau',
      author_email='andrei@5monkeys.se',
      description='Ruby on Rails workflow for Django',
      keywords='django rails',
      url='http://github.com/andreif/django-rails',
      license='MIT',
      install_requires=[],
      )
