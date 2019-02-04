# This file is part of the neovim-pytc-example. It is currently hosted at
# https://github.com/mvilim/neovim-pytc-example
#
# neovim-pytc-example is licensed under the MIT license. A copy of the license can be
# found in the root folder of the project.

from setuptools import setup
from os import path


install_requires = [
    'pylibtermkey>=0.2.2',
    'pynvim>=0.3',
    ]


with open(path.join(path.abspath(path.dirname(__file__)), 'README.md')) as fh:
    long_description = fh.read()


setup(
    name='neovim-pytc-example',
    version='0.0.1',
    author='Michael Vilim',
    author_email='michael.vilim@gmail.com',
    url='https://github.com/mvilim/neovim-pytc-example',
    description='Example of using the Neovim API in a a Python terminal client',
    long_description=long_description,
    packages=['neovim_pytc'],
    entry_points = {
        'console_scripts': ['neovim_pytc=neovim_pytc.neovim_pytc:run_cli'],
    },
    install_requires=install_requires,
    )
