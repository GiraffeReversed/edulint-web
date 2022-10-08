import os


def full_path(upload_folder: str, filename: str) -> str:
    return os.path.join(upload_folder, filename)


def code_path(upload_folder: str, code_hash: str) -> str:
    return full_path(upload_folder, code_hash) + ".py"


def problems_path(upload_folder: str, code_hash: str) -> str:
    return full_path(upload_folder, code_hash) + ".json"
