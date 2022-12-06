import argparse
import json
import sys
from pathlib import Path
from typing import Callable, List, Union

__all__ = ["pckg_versioner"]


class WrongVersionFormatError(Exception):
    """Version has wrong format"""


def read_version_info(filename: Union[str, Path]) -> List[int]:
    contents = json.load(open(filename, "r"))
    if "version_info" not in contents:
        raise WrongVersionFormatError(
            f"Excpected to find 'version_info' in {filename}. Got: {list(contents.keys())}"
        )
    return contents["version_info"]  # Major, minor, patch


def read_version(filename: Union[str, Path]) -> str:
    contents = json.load(open(filename, "r"))
    if "version" not in contents:
        raise WrongVersionFormatError(
            f"Excpected to find 'version' in {filename}. Got: {list(contents.keys())}"
        )
    return contents["version"]  # Major, minor, patch


def update_version_info(version_info: List[int], identifier: str) -> List[int]:
    if identifier in ["major"]:
        version_info[0] += 1
        version_info[1] = 0
        version_info[2] = 0
    elif identifier in ["minor"]:
        version_info[1] += 1
        version_info[2] = 0
    elif identifier in ["patch"]:
        version_info[2] += 1
    else:
        raise ValueError(f"Expected ['major', 'minor', 'patch']. Got: '{identifier}'")

    return version_info


def write_version(filename: Union[str, Path], version_info: List[int]) -> None:
    json.dump(
        dict(version=".".join(list(map(str, version_info))), version_info=version_info),
        open(filename, "w"),
    )


def find_version_path(args: argparse.Namespace) -> Path:
    def handle_dir(dir_: Union[Path, str]) -> Path:
        dir_ = Path(dir_)
        vfiles = sorted(dir_.rglob("version.json"))

        if len(vfiles) == 1:
            return vfiles[0]

        if len(vfiles) > 1:
            print(
                f"WARNING: Found multiple version files ({len(vfiles)}). Using first instance of 'version.json'"
            )
            return vfiles[0]

        if len(vfiles) == 0:
            msg = f"No version found. Creating new version in {dir_} ."
            if "force" in args and args.force:
                print("WARNING:", msg)
                write_version(dir_ / "version.json", [1, 0, 0])
            else:
                print("DRY-RUN:", msg)

            sys.exit(0)

        raise ValueError

    if args.filename is not None:
        filename = Path(args.filename)
        if filename.is_file():
            return filename
        if filename.is_dir():
            return handle_dir(filename)
        if not filename.exists():
            raise FileNotFoundError(f"{filename} does not exist")

    return handle_dir(".")


class ArgsView(argparse.Namespace):
    filename: str
    force: bool
    op: Callable


def view_version_func(args: ArgsView):
    filename = find_version_path(args)
    print("File:", filename.absolute())
    print("Version:", read_version(filename=filename))


class ArgsUpdate(argparse.Namespace):
    filename: str
    identifier: str
    force: bool
    op: Callable


def update_version_func(args: ArgsUpdate):
    identifier = args.identifier
    force = args.force

    filename = find_version_path(args)

    print("File:", filename.absolute())

    version_info = read_version_info(filename=filename)

    print("Old version:", ".".join(list(map(str, version_info))))

    version_info = update_version_info(version_info, identifier)

    print("New version:", ".".join(list(map(str, version_info))))

    if force:
        write_version(filename=filename, version_info=version_info)
        print(f"Updated version.")
    else:
        print(f"DRY-RUN: Updated version.")


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.set_defaults(
        op=lambda *args, **kwargs: print(
            r"Please select a command from {info, bump} and run again..."
        )
    )
    subparsers = parser.add_subparsers(
        description="Shows version and version file or Updates version"
    )
    parser_view = subparsers.add_parser("info")

    def add_common_args(parser_):
        parser_.add_argument(
            "-f",
            "--filename",
            type=str,
            default=None,
            dest="filename",
            help="Version file path",
        )
        parser_.add_argument(
            "--force",
            dest="force",
            action="store_true",
            help="Bump version",
        )

    parser_view.set_defaults(op=view_version_func)
    add_common_args(parser_view)

    parser_update = subparsers.add_parser("bump")
    parser_update.add_argument(
        "identifier",
        choices={"major", "minor", "patch"},
        help="Bump the version identifier",
    )

    add_common_args(parser_update)
    parser_update.set_defaults(op=update_version_func)
    return parser


def pckg_versioner():
    args = get_parser().parse_args()
    # print('Args:',args)
    args.op(args)


if __name__ == "__main__":
    pckg_versioner()

# ENDFILE
