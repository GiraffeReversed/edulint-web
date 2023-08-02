import requests
import toml
import subprocess
import sys
import os
from typing import Dict, Any, List, Optional
from collections import defaultdict

from utils import Version


CONFIG = {
    "CODE_FOLDER": "codes",
    "ANALYSIS_FOLDER": "analyses",
    "VERSIONS_FOLDER": "versions",
    "LINTER_FOLDER_PREFIX": "edulint",
    "EXPLANATIONS": "explanations.json",
}


def _fully_released_versions(data: Dict[str, Any]) -> List[Version]:
    releases = data["releases"]

    version_ids = [v for v in releases.keys()]
    valid_versions: List[Version] = []

    for version_id in version_ids:
        has_some_builds: bool = bool(len(releases[version_id]))
        is_yanked: bool = any([x.get('yanked') for x in releases[version_id]])
        version_parsed: Optional[Version] = Version.parse(version_id)

        if has_some_builds and not is_yanked and version_parsed:
            valid_versions.append(version_parsed)

    return valid_versions


def _only_last_patch_of_each_minor(versions: List[Version]) -> List[Version]:
    major_minor: Dict[str, Version] = defaultdict(list)
    for version in versions:
        major_minor[f"{version.major}.{version.minor}"].append(version)
    for key in major_minor:
        major_minor[key].sort(reverse=True)
    return [major_minor[key][0] for key in major_minor]


def get_versions() -> List[Version]:
    edulint_info = requests.get("https://pypi.org/pypi/edulint/json").json()
    version_ids: List[Version] = _fully_released_versions(edulint_info)
    version_ids = _only_last_patch_of_each_minor(version_ids)
    version_ids = [v_id for v_id in version_ids if v_id.major >= 3 or (v_id.major == 2 and v_id.minor >= 7)]

    return version_ids


def prepare_config(config, versions):
    config = config.copy()
    config["VERSIONS"] = [str(v) for v in versions]

    with open("config.toml", "w") as f:
        f.write(toml.dumps(config))


def prepare_packages(config, versions):
    for version in versions:
        version_folder = os.path.join(config['VERSIONS_FOLDER'], f"{config['LINTER_FOLDER_PREFIX']}_{version.name()}")
        subprocess.check_call(f"{sys.executable} -m pip install edulint=={version} --target={version_folder}".split())


if __name__ == "__main__":
    versions = get_versions()

    prepare_packages(CONFIG, versions)
    prepare_config(CONFIG, versions)
