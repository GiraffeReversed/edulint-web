import toml

CONFIG = {
    "CODE_FOLDER": "codes",
    "ANALYSIS_FOLDER": "analyses",
    "LINTER_FOLDER_PREFIX": "edulint",
    "EXPLANATIONS": "explanations.json",
    "DATABASE_FOLDER": "databases",
    "DATABASE": "db.db",
}


def prepare_config(config):
    with open("config.toml", "w") as f:
        f.write(toml.dumps(config))


if __name__ == "__main__":
    prepare_config(CONFIG)
