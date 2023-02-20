import re
import sys
from distutils.command.sdist import sdist as sdist_orig
from pathlib import Path
from setuptools import setup, find_packages

if not sys.version_info >= (3, 9):
    raise RuntimeError("aiohttp_admin doesn't support Python earlier than 3.9")


def read_version():
    regexp = re.compile(r'^__version__\W*=\W*"([\d.abrc]+)"')
    init_py = Path(__file__).parent / "aiohttp_admin" / "__init__.py"
    with init_py.open() as f:
        for line in f:
            match = regexp.match(line)
            if match is not None:
                return match.group(1)
    raise RuntimeError("Cannot find version in aiohttp_admin/__init__.py")


classifiers = (
    "License :: OSI Approved :: Apache Software License",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Development Status :: 3 - Alpha",
    "Topic :: Internet :: WWW/HTTP",
    "Framework :: AsyncIO",
    "Framework :: Aiohttp",
)


class sdist(sdist_orig):
    def run(self):
        import time
        print(time.time())
        self.spawn(["yarn", "install"])
        self.spawn(["yarn", "build"])
        print(time.time())
        print("DONE")
        super().run()


setup(name="aiohttp-admin",
      version=read_version(),
      cmdclass={"sdist": sdist},
      description="admin interface for aiohttp application",
      long_description="\n\n".join((Path("README.rst").read_text(), Path("CHANGES.rst").read_text())),
      classifiers=classifiers,
      url="https://github.com/aio-libs/aiohttp_admin",
      download_url="https://github.com/aio-libs/aiohttp_admin",
      license="Apache 2",
      packages=find_packages(),
      install_requires=("aiohttp>=3.8.2", "aiohttp_security", "aiohttp_session", "pydantic"),
      extras_require={"sa": ["sqlalchemy>=2,<3"]},
      include_package_data=True)
