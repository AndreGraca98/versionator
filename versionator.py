#!/usr/bin/env python

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "MultipleFilesFoundError",
    "Identifiers",
    "Versionator",
    "update_version_info",
    "version2info",
    "info2version",
    "get_latest_tag",
]

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
        if (process.returncode != 0) and (
            "nothing to commit" not in process.stderr.decode() + process.stdout.decode()
        ):
            print(f"{process.stdout.decode()}")
            print(f"{process.stderr.decode()}")
            print(f"Failed '{cmd}' . Rolling back changes")
            subprocess.run(f"git reset {file}", shell=True)
            exit(1)

        cmd = f"git tag -a {version} {prepare_tag_message(tag_message)}"
        process = subprocess.run(cmd, shell=True)
        if process.returncode != 0:
            print(f"Failed '{cmd}' . Rolling back changes")
            subprocess.run("git reset --soft HEAD~", shell=True)
            subprocess.run(f"git reset {file}", shell=True)
            exit(1)

    def _get_version_file(self) -> Path:
        files = list(Path(".").glob("_version.py"))
        if len(files) == 1:
            return files[0]
        if len(files) > 1:
            raise MultipleFilesFoundError(files)

        _help = (
            "Run the following: "
            f"echo '__version__ = \"{DEFAULT_VERSION}\"' > _version.py\n"
        )
        raise FileNotFoundError(f"Could not find _version.py in {Path.cwd()}. {_help}")

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
    group = info_parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--version-info",
        action="store_const",
        const="version-info",
        default=None,
        dest="about",
    )
    group.add_argument(
        "--tag", action="store_const", const="tag", default=None, dest="about"
    )
    group.add_argument(
        "--version", action="store_const", const="version", default=None, dest="about"
    )

    return parser


def get_args(parser: argparse.ArgumentParser) -> argparse.Namespace:
    args = parser.parse_args()
    return args


def main(parser: argparse.ArgumentParser) -> None:
    args = get_args(parser)

    versionator = Versionator()

    if args.action == "bump":
        versionator.bump_version(args.identifier, args.dryrun)

        if args.tag_message is not None:
            versionator.tag(args.tag_message, args.dryrun)

    elif args.action == "tag":
        versionator.tag(args.tag_message, args.dryrun)

    elif args.action == "info":
        if args.about == "version":
            print(versionator.version)
        elif args.about == "version-info":
            print(version2info(versionator.version))
        elif args.about == "tag":
            print(get_latest_tag())


def tab_complete(parser: argparse.ArgumentParser):
    """Bash autocomplete for subcommands and actions.
    This function is called when the script is run with
    the argument BASH_COMPLETION and the argument SUBCOMMANDS or ACTIONS {subcommand}}
    """

    def get_commands_and_options(parser):
        subparsers_and_options = {}
        for action in parser._actions:
            if not isinstance(action, argparse._SubParsersAction):
                continue
            for subparser_name, subparser in action.choices.items():
                options = []
                for option in subparser._actions:
                    if "-h" in option.option_strings:
                        continue
                    if option.choices:
                        options.extend(option.choices)
                    options.extend(option.option_strings)
                subparsers_and_options[subparser_name] = options + ["-h", "--help"]
        return subparsers_and_options

    def __get_commands():
        return " ".join(get_commands_and_options(parser).keys())

    def __get_command_options(subcommand: str):
        return " ".join(get_commands_and_options(parser)[subcommand])

    import sys

    if "COMPLETION" in sys.argv[1:]:
        if "INIT" in sys.argv[1:]:
            print(
                """

# versionator
# START: Bash auto completion for versionator
# Do not edit the following line; it is used by versionator
_versionator_complete() {
    local cur prev
    cur=${COMP_WORDS[COMP_CWORD]}
    prev=${COMP_WORDS[COMP_CWORD - 1]}

    case ${COMP_CWORD} in
    1)
        COMPREPLY=($(compgen -W "$(versionator COMPLETION COMMANDS)" -- ${cur}))
        ;;
    2)
        case ${prev} in
        bump)
            COMPREPLY=($(compgen -W "$(versionator COMPLETION OPTIONS bump)" -- ${cur}))
            ;;
        tag)
            COMPREPLY=($(compgen -W "$(versionator COMPLETION OPTIONS tag)" -- ${cur}))
            ;;
        info)
            COMPREPLY=($(compgen -W "$(versionator COMPLETION OPTIONS info)" -- ${cur}))
            ;;
        *)
            COMPREPLY=()
            ;;
        esac
        ;;
    *)
        COMPREPLY=($(compgen -f -- ${cur}))

        ;;
    esac
}
complete -F _versionator_complete versionator
# END: Bash auto completion for versionator

"""
            )
            exit(0)
        elif "COMMANDS" in sys.argv[1:]:
            if len(sys.argv) in (3, 4):
                print(__get_commands())
                exit(0)

            _help = (
                "Invalid bash completion arguments. Got: "
                f"{sys.argv}. Should be: "
                "'python versionator.py COMPLETION COMMANDS' or "
                "'versionator COMPLETION COMMANDS'"
            )
        elif "OPTIONS" in sys.argv[1:]:
            if len(sys.argv) in (4, 5):
                print(__get_command_options(sys.argv[~0]))
                exit(0)

            _help = (
                "Invalid bash completion arguments. Got: "
                f"{sys.argv}. Should be: "
                "'python versionator.py COMPLETION OPTIONS {subcommand}' or "
                "'versionator COMPLETION OPTIONS {subcommand}'"
            )

        else:
            _help = (
                "Invalid bash completion arguments. Got: "
                f"{sys.argv}. Should be: "
                "'python versionator.py COMPLETION INIT' or "
                "'versionator COMPLETION INIT' or"
                "'python versionator.py COMPLETION COMMANDS' or "
                "'versionator COMPLETION COMMANDS' or "
                "'python versionator.py COMPLETION OPTIONS {subcommand}' or "
                "'versionator COMPLETION OPTIONS {subcommand}'"
            )
        raise ValueError(_help)


if __name__ == "__main__":
    parser = get_parser()
    tab_complete(parser)
    main(parser)
