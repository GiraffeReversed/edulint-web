import requests
import toml
import subprocess
import sys
import os
from collections import defaultdict
from typing import Dict, Any, List

from utils import Version


CONFIG = {
    "CODE_FOLDER": "codes",
    "ANALYSIS_FOLDER": "analyses",
    "VERSIONS_FOLDER": "versions",
    "LINTER_FOLDER_PREFIX": "edulint",
    "EXPLANATIONS": "explanations.json",
}

def _filter_versions(data: Dict[str, Any]) -> List[str]:
    releases = data["releases"]

    version_ids = [v for v in releases.keys()]
    included_versions: List[str] = []

    for version_id in version_ids:
        has_some_builds: bool = bool(len(releases[version_id]))
        is_yanked: bool = any([x.get('yanked') for x in releases[version_id]])
        
        if has_some_builds and not is_yanked:
            included_versions.append(version_id)
    
    return included_versions


def get_versions():
    def filter(versions):
        return [v for v in versions if v >= Version("1.0.0")]

    edulint_info = requests.get("https://pypi.org/pypi/edulint/json").json()
    version_ids = _filter_versions(edulint_info)

    return filter([Version(v) for v in version_ids])


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
