# Version Updater

![badge](https://img.shields.io/github/package-json/v/AndreGraca98/version-updater?filename=version_updater%2Fversion.json&label=version-updater&logo=python&logoColor=yellow)

version-updater is a simple and easy to use tool to update package versions using a file named version.json to track your project versions.

- [Version Updater](#version-updater)
  - [Requirements](#requirements)
  - [Install](#install)
  - [Usage](#usage)
  - [TODO](#todo)

## Requirements

- python

## Install

```bash
# Create env
env_name=myenv
conda create -n $env_name python=3.7 -y
conda activate $env_name

# Install package
pip install git+https://github.com/AndreGraca98/version-updater.git

source ~/.profile

```

## Usage

```bash
# View the current version
$ VersionUpdater info
File: /home/brisa/cmd-line-utils/version_updater/version.json
Version: 1.0.0

# View the current version for a specific folder/file
$ VersionUpdater info -f [FILENAME or DIRNAME]

# if flag --force is not used the version is not updated. Only view what would happen
# Bump version major
$ VersionUpdater bump major
File: /home/brisa/cmd-line-utils/version_updater/version.json
Old version: 1.0.0
New version: 2.0.0
DRY-RUN: Updated version.

# Bump version major
$ VersionUpdater bump major --force
File: /home/brisa/cmd-line-utils/version_updater/version.json
Old version: 1.0.0
New version: 2.0.0
Updated version.

# Bump version minor
$ VersionUpdater bump minor --force
File: /home/brisa/cmd-line-utils/version_updater/version.json
Old version: 2.0.0
New version: 2.1.0
Updated version.

# Bump version patch
$ VersionUpdater bump patch --force
File: /home/brisa/cmd-line-utils/version_updater/version.json
Old version: 2.1.0
New version: 2.1.1
Updated version.



```

## TODO
  
  1. [ ] add tests
  1. [ ] improve find_version_path function to better handle file/dir inputs
