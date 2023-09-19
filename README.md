# Versionator

![badge](https://img.shields.io/github/v/tag/AndreGraca98/version-updater?logo=python&logoColor=yellow&label=version)

`versionator` is a simple and easy to use tool to update package versions using a file named _version.py to track your project versions and optionaly also tag the repo.

- [Versionator](#versionator)
  - [Requirements](#requirements)
  - [Install](#install)
  - [Usage](#usage)
    - [1. info](#1-info)
    - [2. bump](#2-bump)
    - [3. tag](#3-tag)

## Requirements

- python

## Install

```bash
# Install the tool
pip install git+https://github.com/AndreGraca98/versionator.git

# Add tab-completion
echo '[ -f ~/bin/versionator ] && source /dev/stdin <<<"$(versionator COMPLETION INIT)"' >>~/.bash_completion
```

## Usage

### 1. info

  ```bash
  # View the current version
  $ versionator info --version
  2.0.0
  $ versionator info --version-info
  [2, 0, 0]
  $ versionator info --tag
  2.0.0
  ```

### 2. bump

Will raise `FileNotFoundError` if version does not exist.

```bash
$ versionator bump fix
FileNotFoundError: Could not find _version.py in <your-repo>. Run the following: echo '__version__ = "0.0.0"' > _version.py

# Update version to the next patch version
$ versionator info version
2.0.0
$ versionator bump fix
$ versionator info version
2.0.1

# if flag -d/--dryrun is used, the version is not updated. Only view what would happen
$ versionator bump fix --dryrun
Updating version "2.0.0" to "2.0.1"

# if flag -t/--tag is used, update version and also tag the repo with the version
$ versionator info version
2.0.0
$ versionator info tag
2.0.0
$ versionator bump fix --tag
$ versionator info version
2.0.1
$ versionator info tag
2.0.1
```

### 3. tag

Will raise `RuntimeError` if the version is already tagged.

```python
# Tag the repo (note: the current version must be different from the latest tag)
$ versionator tag
```
