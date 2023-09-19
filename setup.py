import subprocess
from pathlib import Path

from setuptools import setup
from setuptools.command.install import install

from _version import __version__

script = f"""
chmod +x versionator.py
mkdir -p {Path.home()}/bin/
cp versionator.py {Path.home()}/bin/versionator
"""


class PostInstallCommand(install):
    """Pre-installation for installation mode."""

    def run(self):
        super().run()
        for cmd in script.split("\n"):
            if cmd.strip():
                subprocess.run(cmd, shell=True, check=True)


setup(
    name="versionator",
    version=__version__,
    description="versionator is a simple and easy to use tool to "
    "update package versions using a file named _version.py to track "
    "your project versions and optionaly tag it in git.",
    author="André Graça",
    author_email="andrepgraca+versionator@gmail.com",
    platforms="Python",
    cmdclass={
        "install": PostInstallCommand,
    },
)
