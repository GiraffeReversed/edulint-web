import os
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass
import functools
from flask_caching import Cache


@dataclass(init=False, order=True)
class Version:

    _Version = Tuple[int, int, int]
    version: _Version

    def __init__(self, version_raw):
        self.version = tuple([int(v) for v in version_raw.split(".")])

    def name(self) -> str:
        return "_".join(map(str, self.version))

    def __str__(self) -> str:
        return ".".join(map(str, self.version))

    def dir(self, prefix: str) -> str:
        return f"{prefix}_{self.name()}"

    @staticmethod
    def is_valid(version_raw: str) -> bool:
        version_split = version_raw.split(".")

        return len(version_split) == 3 and all(v.isdecimal() for v in version_split)

    @staticmethod
    def parse(version_raw: str) -> Optional["Version"]:
        if not Version.is_valid(version_raw):
            return None

        return Version(version_raw)


def full_path(upload_folder: str, filename: str, version: Optional[Version] = None) -> str:
    version_name = f"_{version.name()}" if version is not None else ""
    return os.path.join(upload_folder, f"{filename}{version_name}")


def code_path(config: Dict[str, str], code_hash: str) -> str:
    return full_path(config["CODE_FOLDER"], code_hash) + ".py"


def problems_path(config: Dict[str, str], code_hash: str, version: Version) -> str:
    return full_path(config["ANALYSIS_FOLDER"], code_hash, version) + ".json"


def explanations_path(config: Dict[str, str]) -> str:
    return os.path.join("static", config["EXPLANATIONS"])


@functools.lru_cache
def get_available_versions(versions_raw: List[str]) -> List[Version]:
    return [Version(v) for v in versions_raw]


def get_latest(versions: List[Version]) -> Version:
    return max(versions)


cache_config = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300
}
cache = Cache()
