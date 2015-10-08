"""
Flask-Profiler
-------------

Flask Profiler

Links
`````

* `development version <http://github.com/muatik/flask-profiler/>`

"""
import sys
from setuptools import setup

tests_require = [
    "Flask-Testing"
]

install_requires = [
    'Flask'
]

setup(
    name='Flask-Profiler',
    version='0.1',
    url='https://github.com/muatik/flask-profiler',
    license='MIT',
    author='Mustafa Atik',
    author_email='muatik@gmail.com',
    description='API endpoint profiler for Flask framework',
    long_description=open('README.md').read(),
    packages=['flask_profiler'],
    test_suite="unittests.suite",
    zip_safe=False,
    platforms='any',
    install_requires=install_requires,
    tests_require=tests_require,
    classifiers=[
        'Development Status :: 1 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
