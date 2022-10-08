import os
from typing import Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass(init=False, order=True)
class Version:

    version: Tuple[int, int, int]

    def __init__(self, version_raw):
        self.version = Version.parse(version_raw)

    def name(self) -> str:
        return "_".join(self.version)

    def version_str(self) -> str:
        return ".".join(self.version)

    def dir(self, prefix: str) -> str:
        return f"{prefix}_{self.name()}"

    @staticmethod
    def parse(version_raw: str) -> Optional["Version"]:
        version_split = version_raw.split(".")

        if len(version_split) != 3 or not all(v.is_decimal() for v in version_split):
            return None

        return tuple([int(v) for v in version_split])


def full_path(upload_folder: str, filename: str, version: Optional[Version] = None) -> str:
    version_name = f"_{version.name()}" if version is not None else ""
    return os.path.join(upload_folder, f"{filename}{version_name}")


def code_path(config: Dict[str, str], code_hash: str) -> str:
    return full_path(config["CODE_FOLDER"], code_hash) + ".py"


def problems_path(config: Dict[str, str], code_hash: str, version: Version) -> str:
    return full_path(config["ANALYSIS_FOLDER"], code_hash, version) + ".json"
