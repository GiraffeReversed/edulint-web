import requests
import toml
import subprocess
import sys
import os

from utils import Version


CONFIG = {
    "CODE_FOLDER": "codes",
    "ANALYSIS_FOLDER": "analyses",
    "VERSIONS_FOLDER": "versions",
    "LINTER_FOLDER_PREFIX": "edulint",
    "EXPLANATIONS": "explanations.json",
}


def get_versions():
    def filter(versions):
        return [v for v in versions if v >= Version("1.0.0")]

    edulint_info = requests.get("https://pypi.org/pypi/edulint/json").json()
    return filter([Version(v) for v in edulint_info["releases"].keys()])


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
