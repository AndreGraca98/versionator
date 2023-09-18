import subprocess
from pathlib import Path

from setuptools import setup
from setuptools.command.install import install

from _version import __version__

script = f"""
chmod +x update_version.py
cp update_version.py versionator
mkdir -p {Path.home()}/bin/
cp -r version_updater {Path.home()}/bin/
cp versionator {Path.home()}/bin/
"""


class PostInstallCommand(install):
    """Pre-installation for installation mode."""

    def run(self):
        install.run(self)
        for cmd in script.split("\n"):
            if cmd.strip():
                subprocess.run(cmd, shell=True, check=True)


setup(
    name="version-updater",
    version=__version__,
    description="version-updater is a simple and easy to use tool to "
    "update package versions using a file named _version.py to track "
    "your project versions and optionaly tag it in git.",
    author="André Graça",
    author_email="andre.p.g@sapo.pt",
    platforms="Python",
    packages=["version_updater"],
    cmdclass={
        "install": PostInstallCommand,
    },
)
