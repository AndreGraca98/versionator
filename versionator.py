#!/usr/bin/env python

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

DEFAULT_VERSION = "0.0.0"


class Identifiers:
    MAJOR = ("major", "big")
    MINOR = ("minor", "small")
    PATCH = ("patch", "fix", "bugfix")

    @classmethod
    def names(cls) -> tuple[str, ...]:
        return cls.MAJOR + cls.MINOR + cls.PATCH

    @classmethod
    def names_repr(cls) -> str:
        return ", ".join(list(map(repr, cls.names())))


@dataclass
class MultipleFilesFoundError(OSError):
    files: list[Path]

    def __str__(self):
        files = ", ".join(map(str, self.files))
        return f"Found more than one file with the same name: {files}"


def find_version_file_path() -> Path:
    files = list(Path(".").rglob("_version.py"))
    if len(files) == 1:
        return files[0]
    if len(files) > 1:
        raise MultipleFilesFoundError(files)

    _help = (
        f"Run the following: echo '__version__ = \"{DEFAULT_VERSION}\"' > _version.py\n"
    )
    raise FileNotFoundError(f"Could not find _version.py. {_help}")


def extract_version_from_file(file: Path) -> str:
    version_file_content = file.read_text()
    match = re.compile(r'__version__ = "(?P<version>\d+\.\d+\.\d+)"').match(
        version_file_content
    )
    if not match:
        raise ValueError("Could not find version in _version.py")

    version = match.groupdict()["version"]
    return version


def update_version_file(file: Path, version: str, new_version: str) -> None:
    current_content = file.read_text()
    new_content = current_content.replace(
        f'__version__ = "{version}"', f'__version__ = "{new_version}"'
    )
    file.write_text(new_content)


def tag(file: Path, version: str, tag_message: str) -> None:
    def prepare_tag_message(msg: str) -> str:
        msg_lines = msg.split("\n")
        msg_lines = [line.strip() for line in msg_lines if line.strip()]
        msg = " ".join(f'-m "{line}"' for line in msg_lines)
        return msg

    # Check if version was updated/is waiting to be committed
    proc = subprocess.run(f"git status {file}", shell=True, capture_output=True)
    if "nothing to commit, working tree clean" in proc.stdout.decode():
        raise RuntimeError("Version was not updated for some reason.")

    # Add, commit, tag . Return code 0 means success
    assert 0 == subprocess.call(f"git add {file}", shell=True)
    assert 0 == subprocess.call('git commit -m "chore: updated version"', shell=True)
    assert 0 == subprocess.call(
        f"git tag -a {version} {prepare_tag_message(tag_message)}", shell=True
    )


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


def get_previous_tag() -> str:
    return (
        subprocess.run(
            "git describe --abbrev=0 --tags", shell=True, capture_output=True
        )
        .stdout.decode()
        .strip("\n")
    )


def main() -> None:
    parser = get_parser()
    args = get_args(parser)
    print(args)

    VERSION_FILE = find_version_file_path()

    version = extract_version_from_file(VERSION_FILE)
    version_info = version2info(version)

    if args.action == "bump":
        new_version_info = update_version_info(version_info, args.identifier)
        new_version = info2version(new_version_info)

        if args.dry_run:
            print("Updating version from", version, "to", new_version)
        else:
            update_version_file(VERSION_FILE, version, new_version)

        if args.tag_message is not None:
            if args.dry_run:
                print(
                    "Tagging version", new_version, " with message:", args.tag_message
                )
            else:
                tag(VERSION_FILE, new_version, args.tag_message)

    if args.action == "tag":
        if args.dry_run:
            print("Tagging version", version, " with message:", args.tag_message)
        else:
            tag(VERSION_FILE, version, args.tag_message)
        return


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Update version and tag it with a message"
    )

    sub_parser = parser.add_subparsers(dest="action", required=True)
    update_parser = sub_parser.add_parser("bump")
    update_parser.add_argument(
        "identifier",
        type=str,
        choices=Identifiers.names(),
        help="Which part of the version to update",
    )
    update_parser.add_argument(
        "-t",
        "--tag",
        type=str,
        nargs="?",
        const="",
        default=None,
        dest="tag_message",
        help="Tag the version with a message",
    )
    tag_parser = sub_parser.add_parser("tag")
    tag_parser.add_argument(
        "tag_message",
        type=str,
        nargs="?",
        default="",
        help="Tag the version with a message",
    )
    update_parser.add_argument("-d", "--dry-run", action="store_true", help="Dry run")
    tag_parser.add_argument("-d", "--dry-run", action="store_true", help="Dry run")
    parser.add_argument("-d", "--dry-run", action="store_true", help="Dry run")

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
