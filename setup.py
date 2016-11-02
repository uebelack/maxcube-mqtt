# -*- coding: utf-8 -*-
from setuptools import setup


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='maxcube-mqtt',
    version='0.0.1',
    description='Control your eQ-3/ELV MAX! Cube with MQTT',
    long_description=readme,
    author='David Uebelacker',
    author_email='david@uebelacker.ch',
    url='https://github.com/goodfield/maxcube-mqtt.git',
    license=license,
    packages=['maxcubemqtt'],
    install_requires=['maxcube-api'],
    scripts=['bin/maxcube-mqtt']
)
