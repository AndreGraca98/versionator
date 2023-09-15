import argparse
import json
import subprocess
from pathlib import Path
from typing import Callable, List, Union

__all__ = [
    "pckg_versioner",
    "read_version_info",
    "read_version",
]

# TODO: guard clause all nested ifs
# TODO: Improve prints
class WrongVersionFormatError(Exception):
    """Version has wrong format"""


def read_version_info(filename: Union[str, Path]) -> List[int]:
    filename = Path(filename).absolute().resolve()
    contents = json.load(open(filename, "r"))
    if "version_info" not in contents:
        raise WrongVersionFormatError(
            f"Excpected to find 'version_info' in {filename}. Got: {list(contents.keys())}"
        )
    return contents["version_info"]  # Major, minor, patch


def read_version(filename: Union[str, Path]) -> str:
    filename = Path(filename).absolute().resolve()
    contents = json.load(open(filename, "r"))
    if "version" not in contents:
        raise WrongVersionFormatError(
            f"Excpected to find 'version' in {filename}. Got: {list(contents.keys())}"
        )
    return contents["version"]  # Major, minor, patch


def update_version_info(version_info: List[int], identifier: str) -> List[int]:
    if identifier.lower() in ["major"]:
        version_info[0] += 1
        version_info[1] = 0
        version_info[2] = 0
    elif identifier.lower() in ["minor"]:
        version_info[1] += 1
        version_info[2] = 0
    elif identifier.lower() in ["patch"]:
        version_info[2] += 1
    else:
        raise ValueError(
            f"Expected ['major', 'minor', 'patch']. Got: '{identifier.lower()}'"
        )

    return version_info


def write_version(filename: Union[str, Path], version_info: List[int]) -> None:
    json.dump(
        dict(version=".".join(list(map(str, version_info))), version_info=version_info),
        open(filename, "w"),
    )


def find_version_path(
    filename: Union[str, Path], force: bool, tag: bool = False
) -> Path:
    def handle_dir(dir_: Union[Path, str]) -> Path:
        dir_ = Path(dir_).resolve()
        vfiles = sorted(dir_.rglob("version.json"))

        if len(vfiles) == 1:
            return vfiles[0]

        if len(vfiles) > 1:
            print(
                f"WARNING: Found multiple version files ({len(vfiles)}). Using first instance of 'version.json'"
            )
            return vfiles[0]

        # if len(vfiles) == 0
        msg = f"No version found. Creating new version in {dir_}"
        if force and tag:
            print("WARNING:", msg)
            write_version(dir_ / "version.json", [1, 0, 0])

            code = subprocess.run(f"cd {dir_}; git tag v1.0.0", shell=True)
            if code.returncode == 0:
                print(f"Added repo git tag 'v1.0.0'")
                print("Repo git tags:")
                subprocess.run(f"cd {dir_}; git tag", shell=True)
            else:
                print(f"ERROR: Make sure the folder {dir_} is a valid git repo")

        elif force:
            print("WARNING:", msg)
            write_version(dir_ / "version.json", [1, 0, 0])

        elif tag:
            print("DRYRUN:", msg)
            print("Repo git tags:")
            code = subprocess.run(f"cd {dir_}; git tag", shell=True)
            if code.returncode != 0:
                print(f"ERROR: Make sure the folder {dir_} is a valid git repo")

        else:
            print("DRYRUN:", msg)

        exit(0)

    if filename is None:
        return handle_dir(".")

    filename = Path(filename)

    if filename.is_file():
        return filename

    if filename.is_dir():
        return handle_dir(filename)

    if not filename.exists():
        raise FileNotFoundError(f"{filename} does not exist")

    exit(1)


class ArgsView(argparse.Namespace):
    filename: str
    force: bool
    tag: bool
    op: Callable


def view_version_func(args: ArgsView):
    filename = args.filename
    force = args.force
    tag = args.tag

    file = find_version_path(filename=filename, force=force, tag=tag)
    print("File:", file.resolve())
    print("Version:", read_version(filename=file))

    if not tag:
        return

    print("Repo git tags:")
    code = subprocess.run(f"cd {file.parent}; git tag", shell=True)
    if code.returncode != 0:
        print(f"ERROR: Make sure the folder {file.parent} is a valid git repo")


class ArgsUpdate(argparse.Namespace):
    filename: str
    identifier: str
    force: bool
    tag: bool
    op: Callable


def update_version_func(args: ArgsUpdate):
    filename = args.filename
    identifier = args.identifier
    force = args.force
    tag = args.tag

    file = find_version_path(filename=filename, force=force)

    print("File:", file.absolute().resolve())

    version_info = read_version_info(filename=file)

    print(f"Current version: '{'.'.join(list(map(str, version_info)))}'")

    version_info = update_version_info(version_info, identifier)
    version = ".".join(list(map(str, version_info)))

    if force and tag:
        write_version(filename=file, version_info=version_info)
        print(f"Updated version to '{version}'")

        code = subprocess.run(f"cd {file.parent}; git tag v{version}", shell=True)

        if code.returncode == 0:
            print(f"Added repo git tag 'v{version}'")
        else:
            print(f"ERROR: Make sure the folder {file.parent} is a valid git repo")

    elif force:
        write_version(filename=file, version_info=version_info)
        print(f"Updated version to '{version}'")

    elif tag:
        print(f"DRYRUN: Updated version to '{version}'")
        print(f"DRYRUN: Added repo git tag 'v{version}'")
        print("Current repo tags:")
        subprocess.run(f"cd {file.parent}; git tag", shell=True)

    else:
        print(f"DRYRUN: Updated version to '{version}'")


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    def info():
        print(f"WARNING: use the 'info' subcommand for different arguments")
        view_version_func(ArgsView(filename=None, force=False, tag=False))

    parser.set_defaults(op=lambda args: info())
    subparsers = parser.add_subparsers(
        description="Shows version and version file or Updates version"
    )

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
        parser_.add_argument(
            "--tag",
            dest="tag",
            action="store_true",
            help="Add git version tag in format v*.*.*",
        )

    parser_view = subparsers.add_parser("info")
    parser_view.set_defaults(op=view_version_func)
    add_common_args(parser_view)

    parser_update = subparsers.add_parser("bump")
    parser_update.set_defaults(op=update_version_func)
    parser_update.add_argument(
        "identifier",
        choices={"major", "minor", "patch"},
        help="Bump the version identifier",
    )

    add_common_args(parser_update)

    return parser


def pckg_versioner():
    args = get_parser().parse_args()
    # print('Args:',args)
    args.op(args)


if __name__ == "__main__":
    pckg_versioner()

# ENDFILE
