import os

from setuptools import find_packages, setup


def read_file(name):
    with open(name, 'r') as f:
        content = f.read().rstrip('\n')
    return content


def version():
    import odintools
    return odintools.version(read_file('VERSION'), os.environ.get('BUILD_NUMBER'))


setup(
    name='django-rql',
    author='Ingram Micro',
    url='https://connect.cloud.im',
    version_getter=version,
    description='Django RQL Filtering',
    long_description=read_file('README.md'),
    license=read_file('LICENSE'),

    python_requires='>=2.7',
    zip_safe=True,
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_file('requirements/dev.txt').split('\n'),
    tests_require=read_file('requirements/test.txt').replace('-r dev.txt', '').split('\n'),
    setup_requires=['pytest-runner', 'odintools'],
    odintools=True,

    keywords='django rql filter rest api',
    classifiers=[
        'Development Status :: 2',
        'Framework :: Django :: 1.11',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Text Processing :: Filters',
    ]
)
