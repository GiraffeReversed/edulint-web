from flask import redirect, request, current_app, send_from_directory, url_for, Blueprint, render_template

from utils import code_path


bp = Blueprint('web', __name__, template_folder='templates', static_folder='static')


def get_versions():
    versions = current_app.config["VERSIONS"]
    assert versions
    return sorted(versions, reverse=True)


@bp.route("/")
def default_path():
    return redirect("editor", code=302)


@bp.route("/editor", methods=["GET"])
def editor():
    return render_template("editor.html", versions=get_versions())


@bp.route("/editor/code/umime_count_a", methods=["GET"])
def editor_example_umime():
    return redirect(url_for(
        "web.editor_code",
        code_hash="b1f3db5035eec46312dc7e48864836eb0d01b0cd4d01af64190c0a0d860e00ee",
    ))


@bp.route("/editor/code/<string:code_hash>", methods=["GET"])
def editor_code(code_hash: str):
    with open(code_path(current_app.config, code_hash)) as f:
        return render_template("editor.html", textarea=f.read(), versions=get_versions())


@bp.route("/editor/<string:code_hash>", methods=["GET"])
def editor_hash(code_hash: str):
    with open(code_path(current_app.config, code_hash)) as f:
        return render_template("editor.html", textarea=f.read(), versions=get_versions())


@bp.route("/about", methods=["GET"])
def about():
    return render_template("about.html")


@bp.route("/faq", methods=["GET"])
def faq():
    return render_template("faq.html")


@bp.route("/teachers", methods=["GET"])
def teachers():
    return render_template("teachers.html")


@bp.route("/privacy", methods=["GET"])
def privacy():
    return render_template("privacy.html")


# rightfully stolen from
# https://stackoverflow.com/a/14625619
@bp.route('/robots.txt')
def static_from_root():
    print(bp.static_folder, request.path[1:])
    return send_from_directory(bp.static_folder, request.path[1:])
