#!/usr/bin/env python
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages
setup(
    name = "imgserver",
    version = "0.1",
    author = 'Sami Dalouche',
    author_email = 'sami.dalouche@gmail.com',
    license = 'LGPLv3',
    url= 'http://opensource.sirika.com/imgserver',
    description='image conversion and rescaling RESTful web service',
    long_description="imgserver is an image processing web service." 
        "Once images are uploaded using a RESTful web API,  "
        "it is possible to request any derivative of the image based on "
        "a different size or image format.",
    packages = find_packages(exclude=('tests','tests.*')),
    scripts = ['imgserver-standalone.py'],
    include_package_data = True,
    data_files = [('etc', ['etc/imgserver-cherrypy.conf', 'etc/imgserver.conf'])],
    test_suite= "nose.collector",
	install_requires = ['PIL >= 1.1.6','SQLAlchemy == 0.4.8', 'CherryPy == 3.0.2', 'zope.interface >= 3.4.0', 'nose >= 0.10.4', 'mox >= 0.5.0', 'pysqlite >= 2.5.5'],
)