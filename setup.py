import re
import sys
from distutils.command.build import build as _build
from pathlib import Path
from setuptools import setup, find_packages
from setuptools.command.bdist_egg import bdist_egg as _bdist_egg

if not sys.version_info >= (3, 9):
    raise RuntimeError("aiohttp_admin doesn't support Python earlier than 3.9")


class bdist_egg(_bdist_egg):
    def run(self):
        self.run_command("build_js")
        _bdist_egg.run(self)


class build_js(setuptools.Command):
    description = "Build JS"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.spawn(["yarn", "install"])
        self.spawn(["yarn", "build"])


class build(_build):
    sub_commands = _build.sub_commands + [("build_js", None)]


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


class AdminInstall(install):
    def run(self):
        self.spawn(["yarn", "install"])
        self.spawn(["yarn", "build"])
        super().run()


setup(name="aiohttp-admin",
      version=read_version(),
      cmdclass={"bdist_egg": bdist_egg, "build": build, "build_js": build_js},
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
