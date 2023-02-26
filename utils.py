import os
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass
import functools

from packaging import version as packaging_version
from flask_caching import Cache


@dataclass
class Version(packaging_version.Version):
    def __init__(self, version: str) -> None:
        super().__init__(version)

    def is_not_full_release(self) -> bool:
        return not(self.is_prerelease or self.is_postrelease or self.is_devrelease)

    def name(self) -> str:
        return str(self).replace(".", "_")

    def dir(self, prefix: str) -> str:
        return f"{prefix}_{self.name()}"

    def __str__(self) -> str:
        return super().__str__()

    def __repr__(self) -> str:
        return super().__repr__()

    @staticmethod
    def parse(version_raw: str) -> Optional["Version"]:
        try:
            return Version(version_raw)
        except packaging_version.InvalidVersion:
            return None


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
