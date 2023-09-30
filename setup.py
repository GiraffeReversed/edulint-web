import subprocess
import sys
import os
from typing import List

import toml

from utils import Version
from pypi_helper import get_versions

CONFIG = {
    "CODE_FOLDER": "codes",
    "ANALYSIS_FOLDER": "analyses",
    "VERSIONS_FOLDER": "versions",
    "LINTER_FOLDER_PREFIX": "edulint",
    "EXPLANATIONS": "explanations.json",
}


def prepare_config(config, versions: List[Version]):
    config = config.copy()
    config["VERSIONS"] = [str(v) for v in versions]

    with open("config.toml", "w") as f:
        f.write(toml.dumps(config))


def prepare_packages(config, version: Version):
    for version in versions:
        version_folder = os.path.join(config["VERSIONS_FOLDER"], f"{config['LINTER_FOLDER_PREFIX']}_{version.name()}")
        subprocess.check_call(f"{sys.executable} -m pip install edulint=={version} --target={version_folder}".split())


if __name__ == "__main__":
    versions = get_versions("edulint")
    versions = [v_id for v_id in versions if v_id.major >= 2]

    prepare_packages(CONFIG, versions)
    prepare_config(CONFIG, versions)
