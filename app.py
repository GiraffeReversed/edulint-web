from flask import Flask, render_template, redirect, request, flash, send_from_directory, send_file, url_for
from edulint.config.config import get_config
from edulint.linting.linting import lint_one
from edulint.linting.problem import Problem
from edulint.explanations import get_explanations
import os
import json
from hashlib import sha256
from os import path
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix
from markdown import markdown


app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploaded_files"
app.config["EXPLANATIONS"] = "explanations.json"
app.secret_key = "super secret key"

Talisman(app, content_security_policy=None,
         strict_transport_security=False, force_https=False)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)


def full_path(filename: str) -> str:
    return os.path.join(app.config["UPLOAD_FOLDER"], filename)


def code_path(code_hash: str) -> str:
    return full_path(code_hash) + ".py"


def problems_path(code_hash: str) -> str:
    return full_path(code_hash) + ".json"


def explanations_path() -> str:
    return os.path.join("static", app.config["EXPLANATIONS"])


@app.route("/")
def default_path():
    return redirect("editor", code=302)


@app.route("/editor", methods=["GET"])
def editor():
    return render_template("editor.html")


@app.route("/upload_code", methods=["POST"])
def upload_code():
    code = request.get_json()["code"]
    code_hash = sha256(code.encode("utf8")).hexdigest()

    if not path.exists(code_path(code_hash)):
        with open(code_path(code_hash), "w", encoding="utf8") as f:
            f.write(code)

    return {"filename": code_hash}


@app.route("/analyze/<string:code_hash>", methods=["GET"])
def analyze(code_hash: str):
    if not code_hash.isalnum():
        return {"message": "Don't even try"}, 400

    if not path.exists(code_path(code_hash)):
        flash('No such file uploaded')
        return redirect("/editor", code=302)

    if path.exists(problems_path(code_hash)):
        with open(problems_path(code_hash), encoding="utf8") as f:
            return f.read()

    config = get_config(code_path(code_hash), [])
    result = lint_one(code_path(code_hash), config)

    result_json = Problem.schema().dumps(result, indent=2, many=True)
    with open(problems_path(code_hash), "w", encoding="utf8") as f:
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


@app.route("/editor/code/umime_count_a", methods=["GET"])
def editor_example_umime():
    return redirect(url_for(
        "editor_code",
        code_hash="c4bc51f7d34f9340c33e0b3b9dcfd12aa8917fe5a11faa5f6385f5bb41be9fcf",
    ))


@app.route("/editor/code/<string:code_hash>", methods=["GET"])
def editor_code(code_hash: str):
    with open(code_path(code_hash)) as f:
        return render_template("editor.html", textarea=f.read())


@app.route("/about", methods=["GET"])
def about():
    return render_template("about.html")


@app.route("/faq", methods=["GET"])
def faq():
    return render_template("faq.html")


@app.route("/teachers", methods=["GET"])
def teachers():
    return render_template("teachers.html")


# rightfully stolen from
# https://stackoverflow.com/a/14625619
@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
