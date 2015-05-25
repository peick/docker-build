#from distutils.core import setup
from setuptools import setup

setup(name='docker-build',
      version='0.1.1a1',
      description='Docker build tool',
      author='Michael Peick',
      author_email='michael.peick@n-pq.de',
      url='',
      packages=['docker_build'],
      install_requires=[
          'requests>=2.7.0'
      ],
      entry_points={
          'console_scripts': [
              'docker-build = docker_build.cli:main'
          ]
      }
    )
