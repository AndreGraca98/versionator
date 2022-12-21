# Version Updater

![badge](https://img.shields.io/github/package-json/v/AndreGraca98/version-updater?filename=version_updater%2Fversion.json&label=version-updater&logo=python&logoColor=yellow)

version-updater is a simple and easy to use tool to update package versions using a file named version.json to track your project versions and optionaly the repo tag.

- [Version Updater](#version-updater)
  - [Requirements](#requirements)
  - [Install](#install)
  - [Usage](#usage)
    - [1. info](#1-info)
    - [2. bump](#2-bump)
  - [TODO](#todo)

## Requirements

- python

## Install

```bash
# Install package
pip install git+https://github.com/AndreGraca98/version-updater.git

# If $HOME/bin/ is not in the $PATH add it in the ~/.bashrc and reload terminal
printf "\n\n"PATH="\$HOME/bin:\$PATH\n\n\n" >> ~/.bashrc
source ~/.bashrc

```

## Usage

### 1. info

  ```bash
  # View the current version
  $ VersionUpdater
  WARNING: use the 'info' subcommand for different arguments
  File: /home/brisa/version-updater/version_updater/version.json
  Version: 1.1.0

  $ VersionUpdater info
  File: /home/brisa/version-updater/version_updater/version.json
  Version: 1.1.0

  $ VersionUpdater info --tag
  File: /home/brisa/version-updater/version_updater/version.json
  Version: 1.1.0
  Repo git tags:
  v1.0.0
  v1.1.0

  # View the current version for a specific folder/file
  $ VersionUpdater info -f ../basic-tools/ --tag
  File: /home/brisa/basic-tools/basic_tools/version.json
  Version: 1.1.0
  Repo git tags:

  ```

### 2. bump

```bash
# Bump version patch
$ VersionUpdater bump minor --force
File: /home/brisa/version-updater/version_updater/version.json
Current version: '1.0.0'
Updated version to '1.1.0'


# if flag --force is not used the version is not updated. Only view what would happen
$ VersionUpdater bump patch
File: /home/brisa/version-updater/version_updater/version.json
Current version: '1.1.0'
DRYRUN: Updated version to '1.1.1'

$ VersionUpdater bump minor
File: /home/brisa/version-updater/version_updater/version.json
Current version: '1.1.0'
DRYRUN: Updated version to '1.2.0'

$ VersionUpdater bump major
File: /home/brisa/version-updater/version_updater/version.json
Current version: '1.1.0'
DRYRUN: Updated version to '2.0.0'

# Update version and add tag to repo
VersionUpdater bump major --tag
Current version: '1.1.0'
DRYRUN: Updated version to '2.0.0'
DRYRUN: Added repo git tag 'v2.0.0'
Current repo tags:
v1.0.0
v1.1.0
```

## TODO
  
  1. [ ] add tests
  1. [x] improve find_version_path function to better handle file/dir inputs
