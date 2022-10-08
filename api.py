from flask import Flask, redirect, request, flash, send_file
import os
import json
from hashlib import sha256
from os import path
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix
from markdown import markdown
from typing import List
import sys

from edulint.config.config import get_config
from edulint.linting.linting import lint_one
from edulint.linting.problem import Problem
from edulint.explanations import get_explanations
from utils import code_path, problems_path, Version

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploaded_files"
app.config["LINTER_FOLDER_PREFIX"] = "edulint"
app.config["EXPLANATIONS"] = "explanations.json"
app.secret_key = "super secret key"

Talisman(app, content_security_policy=None,
         strict_transport_security=False, force_https=False)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)


def explanations_path() -> str:
    return os.path.join("static", app.config["EXPLANATIONS"])


def get_available_versions() -> List[Version]:
    return []


def get_latest() -> Version:
    return max(Version)


@app.route("/api/upload_code", methods=["POST"])
def upload_code():
    code = request.get_json()["code"]
    code_hash = sha256(code.encode("utf8")).hexdigest()

    if not path.exists(code_path(code_hash)):
        with open(code_path(app.config["UPLOAD_FOLDER"], code_hash), "w", encoding="utf8") as f:
            f.write(code)

    return {"filename": code_hash}


def with_version(version, function, *args, **kwargs):
    linter_dir = os.path.join(os.get_cwd(), version.dir(app.config["LINTER_FOLDER_PREFIX"]))

    original_sys_path = sys.path[:]
    sys.path.insert(0, linter_dir)

    original_pypath = os.environ.get("PYTHONPATH")
    os.environ["PYTHONPATH"] = linter_dir + (f":{original_pypath}" if original_pypath else "")

    function(*args, **kwargs)

    sys.path = original_sys_path
    if original_pypath is None:
        os.environ.pop("PYTHONPATH")
    else:
        os.environ["PYTHONPATH"] = original_pypath

    for module in sys.modules.copy():
        if any(m in module for m in ["edulint", "pylint", "flake8"]):
            sys.modules.pop(module)


def lint(cpath: str) -> List[Problem]:
    config = get_config(cpath, [])
    result = lint_one(cpath, config)

    return result


@app.route("/api/<string:version>/analyze/<string:code_hash>", methods=["GET"])
def analyze(version_raw: str, code_hash: str):
    if not code_hash.isalnum():
        return {"message": "Don't even try"}, 400

    version = Version(version_raw)
    if version is None or version not in get_available_versions():
        return {"message": "Invalid version"}, 404

    cpath = code_path(app.config["UPLOAD_FOLDER"], code_hash)
    ppath = problems_path(app.config["UPLOAD_FOLDER"], code_hash, version)

    if not path.exists(cpath):
        flash('No such file uploaded')
        return redirect("/editor", code=302)

    if path.exists(ppath):
        with open(ppath, encoding="utf8") as f:
            return f.read()

    result = with_version(version, lint, cpath)

    result_json = Problem.schema().dumps(result, indent=2, many=True)
    with open(ppath, "w", encoding="utf8") as f:
        f.write(result_json)

    return result_json


@app.route("/api/<string:version>/analyze", methods=["POST"])
def combine(version: str):
    code_hash = upload_code()["filename"]
    return analyze(version, code_hash)


@ app.before_first_request
def prepare_HTML_explanations():
    exps = with_version(get_latest(), get_explanations)

    HTML_exps = {
        code: {
            key: markdown(
                exps[code][key]) for key in exps[code]
        } for code in exps
    }

    with open(explanations_path(), "w") as f:
        f.write(json.dumps(HTML_exps))


@app.route("/api/explanations", methods=["GET"])
def explanations():
    return send_file(explanations_path())


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
