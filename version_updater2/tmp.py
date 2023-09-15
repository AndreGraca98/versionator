import re
from dataclasses import dataclass
from pathlib import Path


class Identifiers:
    MAJOR = ("major", "big")
    MINOR = ("minor", "small")
    PATCH = ("patch", "fix")

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
    version_files = list(Path(".").rglob("_version.py"))
    if len(version_files) == 1:
        return version_files[0]
    elif len(version_files) > 1:
        raise MultipleFilesFoundError(version_files)

    _help = "Run the following: echo '__version__ = \"1.0.0\"' > _version.py\n"
    raise FileNotFoundError(f"Could not find _version.py. {_help}")


def extract_version_from_file(pyversion_file: Path) -> str:
    version_file_content = pyversion_file.read_text()
    match = re.compile(r'__version__ = "(?P<version>\d+\.\d+\.\d+)"').match(
        version_file_content
    )
    if not match:
        raise ValueError("Could not find version in _version.py")

    version = match.groupdict()["version"]
    return version


def update_version_file(pyversion_file: Path, version: str, new_version: str) -> None:
    current_content = pyversion_file.read_text()
    new_content = current_content.replace(
        f'__version__ = "{version}"', f'__version__ = "{new_version}"'
    )
    pyversion_file.write_text(new_content)


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


VERSION_FILE = find_version_file_path()

version = extract_version_from_file(VERSION_FILE)
version_info = version2info(version)

new_version_info = update_version_info(version_info, "fix")
new_version = info2version(new_version_info)

update_version_file(VERSION_FILE, version, new_version)
