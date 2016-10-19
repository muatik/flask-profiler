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
    'Flask',
    'Flask-HTTPAuth'
]

setup(
    name='flask_profiler',
    version='1.2',
    url='https://github.com/muatik/flask-profiler',
    license=open('LICENSE').read(),
    author='Mustafa Atik',
    author_email='muatik@gmail.com',
    description='API endpoint profiler for Flask framework',
    keywords=[
        'profiler', 'flask', 'performance', 'optimization'
    ],
    long_description=open('README.md').read(),
    packages=['flask_profiler'],
    package_data={
        'flask_profiler': [
            'storage/*',
            'static/dist/fonts/*',
            'static/dist/css/*',
            'static/dist/js/*',
            'static/dist/images/*',
            'static/dist/js/*'
            'static/dist/*',
            'static/dist/index.html',
            ]
        },
    test_suite="tests.suite",
    zip_safe=False,
    platforms='any',
    install_requires=install_requires,
    tests_require=tests_require,
    classifiers=[
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
