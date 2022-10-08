from flask import redirect, request, current_app, send_from_directory, url_for, Blueprint, render_template

from utils import code_path


bp = Blueprint('web', __name__, template_folder='templates')


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
        code_hash="c4bc51f7d34f9340c33e0b3b9dcfd12aa8917fe5a11faa5f6385f5bb41be9fcf",
    ))


@bp.route("/editor/code/<string:code_hash>", methods=["GET"])
def editor_code(code_hash: str):
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


# rightfully stolen from
# https://stackoverflow.com/a/14625619
@bp.route('/robots.txt')
def static_from_root():
    return send_from_directory(bp.static_folder, request.path[1:])
