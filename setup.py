from setuptools import find_packages, setup

VERSION = '0.2.0'

long_description = ''
with open('README.md') as ifp:
    long_description = ifp.read()

setup(
    name='simiotics-lambada',
    version=VERSION,
    packages=find_packages(),
    install_requires=[
        'boto3',
        'simiotics',
    ],
    description='Manage AWS Lambda functions using a Simiotics Function Registry',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Neeraj Kashyap',
    author_email='neeraj@simiotics.com',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python',
    ],
    url='https://github.com/simiotics/lambada',
    entry_points={
        'console_scripts': [
            'lambada = lambada.cli:main'
        ]
    }
)
