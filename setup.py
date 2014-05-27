import os
from setuptools import setup


f = open(os.path.join(os.path.dirname(__file__), 'README.md'))
readme = f.read()
f.close()

setup(
    name='tgm-files',
    version='0.1.1',
    description='Stuff...',
    long_description=readme,
    author="Thorgate",
    author_email='info@thorgate.eu',
    url='https://github.com/Jyrno42/tgmfiles',
    packages=['tgmfiles'],
    include_package_data=True,
    install_requires=[
        'Django',
        'Pillow',
        'python-magic==0.4.6',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)
