try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


import xextract


with open('README.rst') as f:
    readme = f.read()
with open('LICENSE') as f:
    license = f.read()


setup(
    name='xextract',
    version=xextract.__version__,
    description='Python library for parsing and data extraction from HTML.',
    long_description=readme,
    author='Michal "Mimino" Danilak',
    author_email='michal.danilak@gmail.com',
    url='https://github.com/Mimino666/python-xextract',
    keywords='HTML parse parsing extraction extract crawl',
    packages=['xextract',
              'xextract.extractors'],
    include_package_data=True,
    install_requires=['lxml', 'cssselect', 'six'],
    license=license,
    zip_safe=False,
    classifiers=(
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4'
    ),
)
