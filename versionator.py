#!/usr/bin/env python

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

DEFAULT_VERSION = "0.0.0"
COMMIT_MSG = '"chore: update version"'


class Identifiers:
    MAJOR = ("major", "big")
    MINOR = ("minor", "small")
    PATCH = ("patch", "fix", "bugfix")

    @classmethod
    def names(cls) -> tuple[str, ...]:
        return cls.MAJOR + cls.MINOR + cls.PATCH

    @classmethod
    def names_repr(cls) -> str:
        return ", ".join(map(repr, cls.names()))


@dataclass
class MultipleFilesFoundError(OSError):
    files: list[Path]

    def __str__(self):
        files = ", ".join(map(repr, self.files))
        return f"Found more than one file with the same name: {files}"


class Versionator:
    def __init__(self) -> None:
        self.version_path: Path = self._get_version_file()

    @property
    def version(self) -> str:
        return self._extract_version_from_file()

    @property
    def version_info(self) -> list[int]:
        return version2info(self.version)

    def bump_version(self, identifier: str, dryrun: bool = False) -> None:
        file: Path = self.version_path
        version: str = self.version

        new_version_info = update_version_info(self.version_info, identifier)
        new_version: str = info2version(new_version_info)

        if dryrun:
            print(f'Updating version "{version}" to "{new_version}"')
            return

        current_content = file.read_text()
        new_content = current_content.replace(
            f'__version__ = "{version}"', f'__version__ = "{new_version}"'
        )
        file.write_text(new_content)

    def tag(self, tag_message: str, dryrun: bool = False) -> None:
        file: Path = self.version_path
        version: str = self.version

        def prepare_tag_message(msg: str) -> str:
            if not msg:
                return '-m ""'
            msg_lines = msg.split("\n")
            msg_lines = [line.strip() for line in msg_lines if line.strip()]
            msg = " ".join(f'-m "{line}"' for line in msg_lines)
            return msg

        if dryrun:
            print(
                f"Staging {file}, commiting with message {COMMIT_MSG} "
                f"and tagging {version} with '{prepare_tag_message(tag_message)}'"
            )
            return

        # Check if version is valid for tagging
        if get_latest_tag() == version:
            raise RuntimeError(f"Not tagging! Version {version} is already tagged.")

        # Add, commit, tag . Return code 0 means success
        cmd = f"git add {file}"
        process = subprocess.run(cmd, shell=True)
        if process.returncode != 0:
            print(f"Failed '{cmd}' . Rolling back changes")
            exit(1)

        cmd = f"git commit -m {COMMIT_MSG}"
        process = subprocess.run(cmd, shell=True, capture_output=True)
        if (
            process.returncode != 0
            and "nothing to commit" not in process.stderr.decode()
        ):
            subprocess.run(f"git reset {file}", shell=True)
            print(f"Failed '{cmd}' . Rolling back changes")
            exit(1)

        cmd = f"git tag -a {version} {prepare_tag_message(tag_message)}"
        process = subprocess.run(cmd, shell=True)
        if process.returncode != 0:
            subprocess.run("git reset --soft HEAD~", shell=True)
            subprocess.run(f"git reset {file}", shell=True)
            print(f"Failed '{cmd}' . Rolling back changes")
            exit(1)

    def _get_version_file(self) -> Path:
        files = list(Path(".").rglob("_version.py"))
        if len(files) == 1:
            return files[0]
        if len(files) > 1:
            raise MultipleFilesFoundError(files)

        _help = (
            "Run the following: "
            f"echo '__version__ = \"{DEFAULT_VERSION}\"' > _version.py\n"
        )
        raise FileNotFoundError(f"Could not find _version.py. {_help}")

    def _extract_version_from_file(self) -> str:
        file: Path = self.version_path
        version_file_content = file.read_text()
        match = re.compile(r'__version__ = "(?P<version>\d+\.\d+\.\d+)"').match(
            version_file_content
        )
        if not match:
            raise ValueError("Could not find version in _version.py")

        version = match.groupdict()["version"]
        return version


def update_version_info(version_info: list[int], identifier: str) -> list[int]:
    if identifier not in Identifiers.names():
        raise ValueError(
            f"Expected one of {Identifiers.names_repr()}. Got: {identifier.lower()!r}"
        )

    if identifier.lower() in Identifiers.MAJOR:
        version_info[0] += 1
        version_info[1] = 0
        version_info[2] = 0
    elif identifier.lower() in Identifiers.MINOR:
        version_info[1] += 1
        version_info[2] = 0
    elif identifier.lower() in Identifiers.PATCH:
        version_info[2] += 1

    return version_info


def version2info(version: str) -> list[int]:
    return list(map(int, version.split(".")))


def info2version(info: list[int]) -> str:
    return ".".join(list(map(str, info)))


def get_latest_tag() -> str:
    return (
        subprocess.run(
            "git describe --abbrev=0 --tags",
            shell=True,
            capture_output=True,
            check=True,
        )
        .stdout.decode()
        .strip("\n")
    )


def info(about: str) -> None:
    from _version import __version__

    if about == "version":
        print(__version__)
    elif about == "version-info":
        print(version2info(__version__))
    elif about == "tag":
        print(get_latest_tag())


def main() -> None:
    parser = get_parser()
    args = get_args(parser)

    versionator = Versionator()

    if args.action == "bump":
        versionator.bump_version(args.identifier, args.dryrun)

        if args.tag_message is not None:
            versionator.tag(args.tag_message, args.dryrun)

    elif args.action == "tag":
        versionator.tag(args.tag_message, args.dryrun)

    elif args.action == "info":
        info(args.about)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Update version and tag it with a message"
    )
    sub_parser = parser.add_subparsers(dest="action", required=True)

    bump_parser = sub_parser.add_parser("bump")
    bump_parser.add_argument(
        "identifier",
        type=str,
        choices=Identifiers.names(),
        help="Which part of the version to bump",
    )
    bump_parser.add_argument(
        "-t",
        "--tag",
        type=str,
        nargs="?",
        const="",
        default=None,
        dest="tag_message",
        help="Tag the version with a message",
    )
    bump_parser.add_argument("-d", "--dryrun", action="store_true", help="Dry run")

    tag_parser = sub_parser.add_parser("tag")
    tag_parser.add_argument(
        "tag_message",
        type=str,
        nargs="?",
        default="",
        help="Tag the version with a message",
    )
    tag_parser.add_argument("-d", "--dryrun", action="store_true", help="Dry run")

    info_parser = sub_parser.add_parser("info")
    info_sub_parser = info_parser.add_subparsers(required=True, dest="about")
    info_sub_parser.add_parser("version", help="Get the latest version")
    info_sub_parser.add_parser("version-info", help="Get the latest version info")
    info_sub_parser.add_parser("tag", help="Get the latest tag")

    return parser


def get_args(parser: argparse.ArgumentParser) -> argparse.Namespace:
    # args = parser.parse_args(["update","fix"])
    # args = parser.parse_args(["update","fix", "--tag"])
    # args = parser.parse_args(["update","fix","--tag","feat: something"])
    # args = parser.parse_args(["tag"])
    # args = parser.parse_args(["tag", "feat: something"])
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
