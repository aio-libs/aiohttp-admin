import os
import re

from setuptools import find_packages, setup


def read_version():
    regexp = re.compile(r"^__version__\W*=\W*'([\d.abrc]+)'")
    init_py = os.path.join(os.path.dirname(__file__),
                           'motortwit', '__init__.py')
    with open(init_py) as f:
        for line in f:
            match = regexp.match(line)
            if match is not None:
                return match.group(1)
        else:
            msg = 'Cannot find version in motortwit/__init__.py'
            raise RuntimeError(msg)


install_requires = ['aiohttp==3.6.2',
                    'pytz==2019.3',
                    'bcrypt==3.1.7',
                    'aiohttp_session==2.9.0',
                    'aiohttp_admin>=0.0.3',
                    # TODO: Update trafaret to 2.0.x (blocked by issue #487)
                    'trafaret==1.2.0',
                    'aiohttp_jinja2==1.2.0',
                    'pyyaml==5.3.1',
                    'motor==2.1.0',
                    'faker==4.0.2']


setup(name='motortwit',
      version=read_version(),
      description='Blog project example from aiohttp_admin',
      platforms=['POSIX'],
      packages=find_packages(),
      include_package_data=True,
      install_requires=install_requires,
      zip_safe=False)
