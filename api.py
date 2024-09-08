from flask import (
    Blueprint,
    redirect,
    Response,
    request,
    current_app,
    render_template,
    url_for,
)
import werkzeug
import os
from hashlib import sha256
from os import path
import sys
import json
from typing import Optional, List
from pathlib import Path
from loguru import logger
import time
import urllib
import shlex

from utils import (
    code_path,
    problems_path,
    explanations_path,
    Version,
    cache,
    LogCollector,
    get_latest,
    strtobool,
)
from database_management import store_feedback_in_db, store_source_id_in_mapping


bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("", methods=["GET"])
def redirect_to_real_swagger():
    return redirect(url_for("api.get_swagger"))


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
    versions: List[Version] = current_app.config["VERSIONS"]
    # Hotfix for edulint-web and edulint incompatibility, 2023-09-14, TODO: proper fix
    versions = [v_id for v_id in versions if v_id.major >= 3]
    assert versions
    return ["latest"] + list(
        map(str, sorted(versions, reverse=True))
    )  # ["latest", "3.2.1", ...]


# It would be better to move this whole function inside Version but that doesn't have the app context.
def parse_version(version_raw: str) -> Optional[Version]:
    version_raw = get_versions()[1] if version_raw == "latest" else version_raw
    return Version.parse(version_raw)


EXAMPLE_ALIASES = {
    "umime_count_a": "a10b77b1feed3225cceb4b765068965ea482abfc618eee849259f7d1401cd09d"
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
    request_json = request.get_json()
    code = request_json.get("code")

    if code is None:
        return {"message": "No code to upload"}, 400

    code_hash = sha256(code.encode("utf8")).hexdigest()
    source_id = request_json.get("source_id")

    if not path.exists(code_path(current_app.config, code_hash)):
        with open(code_path(current_app.config, code_hash), "w", encoding="utf8") as f:
            f.write(code)

    if source_id is not None:
        store_source_id_in_mapping(source_id, int(time.time()), code_hash)

    return {"hash": code_hash}, 200


def with_version(version: Version, function, *args, **kwargs):
    linter_dir = os.path.join(
        os.getcwd(),
        current_app.config["VERSIONS_FOLDER"],
        version.dir(current_app.config["LINTER_FOLDER_PREFIX"]),
    )

    original_sys_path = sys.path[:]
    sys.path.insert(0, linter_dir)

    original_pypath = os.environ.get("PYTHONPATH")
    os.environ["PYTHONPATH"] = linter_dir + (
        f":{original_pypath}" if original_pypath else ""
    )

    try:
        return function(*args, **kwargs)
    finally:
        sys.path = original_sys_path
        if original_pypath is None:
            os.environ.pop("PYTHONPATH")
        else:
            os.environ["PYTHONPATH"] = original_pypath

        for module in sys.modules.copy():
            if any(m in module for m in ["edulint", "pylint", "flake8"]):
                sys.modules.pop(module)


def lint(version: Version, code_hash: str, url_config: str) -> str:
    def to_json(results: str, log_collector: LogCollector, cpath: str):
        return (
            "{"
            f'"problems": {results},'
            f'"config_errors": {log_collector.json_logs()},'
            f'"hash": "{Path(cpath).stem}"'
            "}"
        )

    def get_use_cached_result():
        use_cached_result_raw = urllib.parse.unquote(
            request.args.get("use-cached-result", default="true")
        ).lower()
        if use_cached_result_raw not in ("true", "false"):
            raise werkzeug.exceptions.BadRequest("Invalid value for use-cached-result")
        return use_cached_result_raw == "true"

    def setup_log_collector():
        log_collector = LogCollector()
        logger.add(
            log_collector,
            level="WARNING",
            format="{level}|{message}",
            colorize=False,
            diagnose=False,
            filter=lambda record: "config" in record["name"],
        )
        return log_collector

    cpath = code_path(current_app.config, code_hash)
    if not path.exists(cpath):
        raise werkzeug.exceptions.NotFound(f"No file with hash {code_hash} uploaded")

    log_collector = setup_log_collector()

    import edulint

    config = edulint.get_config_one(cpath, shlex.split(url_config))
    if config is None:
        return to_json("[]", log_collector, cpath)

    ppath = problems_path(current_app.config, code_hash, version, config)
    if path.exists(ppath) and get_use_cached_result():
        with open(ppath, encoding="utf8") as f:
            return f.read()

    try:
        problems = edulint.lint_one(cpath, config)
    except TimeoutError as e:
        raise werkzeug.exceptions.RequestTimeout(str(e))
    except Exception as e:
        raise werkzeug.exceptions.InternalServerError(str(e))

    problems_json = edulint.Problem.schema().dumps(problems, indent=2, many=True)
    result = to_json(problems_json, log_collector, cpath)

    with open(ppath, "w", encoding="utf8") as f:
        f.write(result)
    return result


@bp.route("/<string:version_raw>/analyze/<string:code_hash>", methods=["GET"])
def analyze(version_raw: str, code_hash: str):
    if not code_hash.isalnum():
        return {"message": "Don't even try"}, 400

    version = parse_version(version_raw)
    if version is None or version not in current_app.config["VERSIONS"]:
        return {"message": "Invalid version"}, 404

    url_config = urllib.parse.unquote(request.args.get("config", default=""))

    try:
        result = with_version(version, lint, version, code_hash, url_config)
    except werkzeug.exceptions.BadRequest as e:
        return {"message": str(e)}, 400
    except werkzeug.exceptions.NotFound as e:
        return {"message": str(e)}, 404
    except werkzeug.exceptions.RequestTimeout as e:
        return {"message": str(e)}, 408
    except werkzeug.exceptions.InternalServerError as e:
        return {"message": str(e)}, 500

    return Response(response=result, status=200, mimetype="application/json")


@bp.route("/<string:version>/analyze", methods=["POST"])
def combine(version: str):
    res, code = upload_code()
    if code != 200:
        return res, code
    return analyze(version, res["hash"])


def get_explanations():
    def get_explanations_import():
        from edulint.explanations import get_explanations

        return get_explanations()

    return with_version(
        get_latest(current_app.config["VERSIONS"]), get_explanations_import
    )


@bp.route("/explanations", methods=["GET"])
@cache.cached(timeout=60 * 60)  # in seconds
def explanations():
    with open(explanations_path(current_app.config)) as f:
        return json.load(f)


def get_explanations_hash(explanations):
    return sha256(json.dumps(sorted(explanations.items())).encode("utf8")).hexdigest()


@bp.route("/explanations/feedback", methods=["POST"])
def give_explanations_feedback():
    json_request = request.get_json()
    explanations = get_explanations()

    feedback = {
        "time": int(time.time()),
        "explanations_hash": get_explanations_hash(explanations),
    }
    for key in (
        "defect_code",
        "good",
        "comment",
        "source_code",
        "source_code_hash",
        "line",
        "user_id",
    ):
        feedback[key] = json_request.get(key)

    if feedback["defect_code"] is None or (
        feedback["good"] is None and feedback["comment"] is None
    ):
        return {"message": "Malformed feedback data"}, 400

    explanation = explanations.get(feedback["defect_code"])
    feedback["explanation"] = (
        json.dumps(explanation) if explanation is not None else None
    )

    feedback["extra"] = "{}"

    store_feedback_in_db(feedback)
    return {"message": "OK"}, 200

@bp.route("/thonny", methods=["POST"])
def thonny():
    content = request.json
    message_type = content.get('type')
    session_id = content.get('session_id', 'thonny:ID_MISSING').split(":")
    # _ = session_id[0] # static "thonny" prefix
    machine_id = session_id[1] # should be present (or ID_FAILURE or ID_MISSING)
    user_id    = session_id[2] if len(session_id) > 2 else "NO_USER_ID"
    file_id    = session_id[3] if len(session_id) > 3 else "NO_FILE_ID"
    # session_id_str = f"thonny:{machine_id}:{user_id}:{file_id}"

    if message_type == "thonny-annoucement-request":
        return {"text": ""}  # Non-empty string would get shown on every startup of Thonny with Thonny-EduLint

    if message_type == "thonny-settings":
        return {
            "force_disable_code_remote_reporting": strtobool(os.environ.get('THONNY_DISABLE_CODE_REMOTE_REPORTING', 'True')),
            "force_disable_result_remote_reporting": strtobool(os.environ.get('THONNY_DISABLE_RESULT_REMOTE_REPORTING', 'True')),
            "force_disable_exception_remote_reporting": strtobool(os.environ.get('THONNY_DISABLE_EXCEPTION_REMOTE_REPORTING', 'True')),
            "enable_first_time_reporting_dialog": strtobool(os.environ.get('THONNY_ENABLE_FIRST_TIME_REPORTING_DIALOG', 'False')),
        }

    if message_type == 'result':
        results: str = content['results']
        return {"error_msg": "Persistance for this data is not yet implemented."}, 501

    if message_type == 'error':
        errors: str = content['errors']
        return {"error_msg": "Persistance for this data is not yet implemented."}, 501

    if message_type == 'code':
        code: str = content['code']
        return {"error_msg": "Persistance for this data is not yet implemented."}, 501

    return {"error_msg": "Unknown message type."}, 400
