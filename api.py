from flask import Blueprint, redirect, request, flash, current_app, render_template, url_for
import werkzeug
import os
from hashlib import sha256
from os import path
import sys
import json
from loguru import logger

from utils import code_path, problems_path, explanations_path, Version, cache, LogCollector


bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route("", methods=["GET"])
def redirect_to_real_swagger():
    return redirect(url_for('api.get_swagger'))


@bp.route("/", methods=["GET"])
def get_swagger():
    return render_template("swagger_index.html")


@bp.route("/openapi.yaml", methods=["GET"])
def get_swagger_yaml():
    return current_app.send_static_file("openapi.yaml")


@bp.route("/swagger_index.js", methods=["GET"])
def get_swagger_js():
    return current_app.send_static_file("swagger_index.js")


@bp.route("/versions", methods=["GET"])
def get_versions():
    versions = current_app.config["VERSIONS"]
    assert versions
    return sorted(map(str, versions), reverse=True)


EXAMPLE_ALIASES = {
    "umime_count_a" : "b1f3db5035eec46312dc7e48864836eb0d01b0cd4d01af64190c0a0d860e00ee"
}


@bp.route("/code/<string:code_name>", methods=["GET"])
def editor_code(code_name: str):
    code_hash = EXAMPLE_ALIASES.get(code_name, code_name)

    if not code_hash.isalnum():
        return {"message": "Don't even try"}, 400

    cpath = code_path(current_app.config, code_hash)
    if not path.exists(cpath):
        return {"message": "No such file"}, 404

    with open(code_path(current_app.config, code_hash)) as f:
        return f.read()


@bp.route("/code", methods=["POST"])
def upload_code():
    code = request.get_json()["code"]
    code_hash = sha256(code.encode("utf8")).hexdigest()

    if not path.exists(code_path(current_app.config, code_hash)):
        with open(code_path(current_app.config, code_hash), "w", encoding="utf8") as f:
            f.write(code)

    return {"hash": code_hash}


def with_version(version: Version, function, *args, **kwargs):
    linter_dir = os.path.join(
        os.getcwd(),
        current_app.config["VERSIONS_FOLDER"],
        version.dir(current_app.config["LINTER_FOLDER_PREFIX"])
    )

    original_sys_path = sys.path[:]
    sys.path.insert(0, linter_dir)

    original_pypath = os.environ.get("PYTHONPATH")
    os.environ["PYTHONPATH"] = linter_dir + (f":{original_pypath}" if original_pypath else "")

    result = function(*args, **kwargs)

    sys.path = original_sys_path
    if original_pypath is None:
        os.environ.pop("PYTHONPATH")
    else:
        os.environ["PYTHONPATH"] = original_pypath

    for module in sys.modules.copy():
        if any(m in module for m in ["edulint", "pylint", "flake8"]):
            sys.modules.pop(module)

    return result


def lint(cpath: str) -> str:
    log_collector = LogCollector()
    logger.add(
        log_collector, level="WARNING", format='{level}|{message}',
        colorize=False, diagnose=False, filter=lambda record: "config" in record["name"]
    )

    import edulint

    config = edulint.get_config_one(cpath, [])
    if config is None:
        return f'{{"problems" : [], "config_errors": {log_collector.json_logs()}}}'

    try:
        result = edulint.lint_one(cpath, config)
    except TimeoutError as e:
        raise werkzeug.exceptions.RequestTimeout(str(e))
    except Exception as e:
        raise werkzeug.exceptions.InternalServerError(str(e))

    result_json = edulint.Problem.schema().dumps(result, indent=2, many=True)

    return f'{{"problems" : {result_json}, "config_errors": {log_collector.json_logs()}}}'


@bp.route("/<string:version_raw>/analyze/<string:code_hash>", methods=["GET"])
def analyze(version_raw: str, code_hash: str):
    if not code_hash.isalnum():
        return {"message": "Don't even try"}, 400

    version = Version.parse(version_raw)
    if version is None or version not in current_app.config["VERSIONS"]:
        return {"message": "Invalid version"}, 404

    cpath = code_path(current_app.config, code_hash)
    ppath = problems_path(current_app.config, code_hash, version)

    if not path.exists(cpath):
        flash('No such file uploaded')
        return redirect("/editor", code=302)

    if path.exists(ppath):
        with open(ppath, encoding="utf8") as f:
            return f.read()

    try:
        result = with_version(version, lint, cpath)
    except werkzeug.exceptions.NotFound as e:
        return {"reason": str(e)}, 404
    except werkzeug.exceptions.RequestTimeout as e:
        return {"reason": str(e)}, 408

    with open(ppath, "w", encoding="utf8") as f:
        f.write(result)

    return result


@bp.route("/<string:version>/analyze", methods=["POST"])
def combine(version: str):
    code_hash = upload_code()["hash"]
    return analyze(version, code_hash)


@bp.route("/explanations", methods=["GET"])
@cache.cached(timeout=60*60)  # in seconds
def explanations():
    with open(explanations_path(current_app.config)) as f:
        return json.load(f)
