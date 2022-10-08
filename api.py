from flask import Flask, redirect, request, flash, send_file
import os
import json
from hashlib import sha256
from os import path
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix
from markdown import markdown

from edulint.config.config import get_config
from edulint.linting.linting import lint_one
from edulint.linting.problem import Problem
from edulint.explanations import get_explanations
from utils import code_path, problems_path

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploaded_files"
app.config["EXPLANATIONS"] = "explanations.json"
app.secret_key = "super secret key"

Talisman(app, content_security_policy=None,
         strict_transport_security=False, force_https=False)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)


def explanations_path() -> str:
    return os.path.join("static", app.config["EXPLANATIONS"])


@app.route("/upload_code", methods=["POST"])
def upload_code():
    code = request.get_json()["code"]
    code_hash = sha256(code.encode("utf8")).hexdigest()

    if not path.exists(code_path(code_hash)):
        with open(code_path(app.config["UPLOAD_FOLDER"], code_hash), "w", encoding="utf8") as f:
            f.write(code)

    return {"filename": code_hash}


@app.route("/analyze/<string:code_hash>", methods=["GET"])
def analyze(code_hash: str):
    if not code_hash.isalnum():
        return {"message": "Don't even try"}, 400

    if not path.exists(code_path(app.config["UPLOAD_FOLDER"], code_hash)):
        flash('No such file uploaded')
        return redirect("/editor", code=302)

    if path.exists(problems_path(app.config["UPLOAD_FOLDER"], code_hash)):
        with open(problems_path(app.config["UPLOAD_FOLDER"], code_hash), encoding="utf8") as f:
            return f.read()

    config = get_config(code_path(app.config["UPLOAD_FOLDER"], code_hash), [])
    result = lint_one(code_path(app.config["UPLOAD_FOLDER"], code_hash), config)

    result_json = Problem.schema().dumps(result, indent=2, many=True)
    with open(problems_path(app.config["UPLOAD_FOLDER"], code_hash), "w", encoding="utf8") as f:
        f.write(result_json)

    return result_json


@app.route("/analyze", methods=["POST"])
def combine():
    code_hash = upload_code()["filename"]
    return analyze(code_hash)


@app.before_first_request
def prepare_HTML_explanations():
    exps = get_explanations()
    HTML_exps = {
        code: {
            key: markdown(
                exps[code][key]) for key in exps[code]
        } for code in exps
    }

    with open(explanations_path(), "w") as f:
        f.write(json.dumps(HTML_exps))


@app.route("/explanations", methods=["GET"])
def explanations():
    return send_file(explanations_path())


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
