import os
from typing import Dict, List, Optional
from dataclasses import dataclass
import functools
import json
import hashlib

from packaging import version as packaging_version
from flask_caching import Cache


@dataclass
class Version(packaging_version.Version):
    def __init__(self, version: str) -> None:
        super().__init__(version)

    def is_not_full_release(self) -> bool:
        return not (self.is_prerelease or self.is_postrelease or self.is_devrelease)

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


def full_path(upload_folder: str, filename: str) -> str:
    return os.path.join(upload_folder, filename)


def code_path(config: Dict[str, str], code_hash: str) -> str:
    return full_path(config["CODE_FOLDER"], code_hash) + ".py"


def problems_path(app_config: Dict[str, str], code_hash: str, edulint_config) -> str:
    path = full_path(app_config["ANALYSIS_FOLDER"], code_hash)
    config_str = json.dumps(edulint_config, sort_keys=True, default=lambda o: str(o))
    config_hash = hashlib.sha256(config_str.encode("utf8")).hexdigest()[:10]
    return f"{path}_{config_hash}.json"


def explanations_path(config: Dict[str, str]) -> str:
    return os.path.join("static", config["EXPLANATIONS"])


@functools.lru_cache
def get_available_versions(versions_raw: List[str]) -> List[Version]:
    return [Version(v) for v in versions_raw]


def get_latest(versions: List[Version]) -> Version:
    return max(versions)


cache_config = {"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300}
cache = Cache()


class LogCollector:
    def __init__(self):
        self.logs = []

    def __call__(self, log):
        level, message = log.split("|", 1)
        self.logs.append({"level": level, "message": message})

    def json_logs(self):
        return json.dumps(self.logs)


# Copied from distutils.util.strtobool, which is deprecated
# Slightly modified to return True/False instead of 1 and 0
def strtobool(val: str) -> bool:
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))
