from setuptools import setup


with open('README.rst', 'r') as f:
    readme = f.read()


setup(
    name='xextract',
    version='0.1.2',
    description='Extract structured data from HTML and XML documents like a boss.',
    long_description=readme,
    author='Michal "Mimino" Danilak',
    author_email='michal.danilak@gmail.com',
    url='https://github.com/Mimino666/python-xextract',
    keywords='HTML parse parsing extraction extract crawl',
    packages=['xextract',
              'xextract.extractors'],
    package_data={'': ['LICENSE']},
    include_package_data=True,
    install_requires=['lxml', 'cssselect', 'six'],
    tests_require=['unittest2', ],
    test_suite='tests',
    license='MIT',
    zip_safe=False,
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
    ),
)
