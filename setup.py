import json
from pathlib import Path
from subprocess import check_call

from setuptools import setup
from setuptools.command.install import install

script = f"""
chmod +x update_version.py
cp update_version.py VersionUpdater
mkdir -p {Path.home()}/bin/
cp -r version_updater {Path.home()}/bin/
cp VersionUpdater {Path.home()}/bin/
"""


class PostInstallCommand(install):
    """Pre-installation for installation mode."""

    def run(self):
        install.run(self)
        for cmd in list(filter(lambda x: x != "", script.split("\n"))):
            print("Runing:", cmd)
            check_call(cmd.split())


setup(
    name="version-updater",
    version=json.load(open("version_updater/version.json"))["version"],
    description="version-updater is a simple and easy to use tool to update package versions.",
    author="André Graça",
    author_email="andre.p.g@sapo.pt",
    platforms="Python",
    packages=["version_updater"],
    cmdclass={
        "install": PostInstallCommand,
    },
)
