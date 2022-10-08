from flask import Flask, render_template, redirect, request, send_from_directory, url_for
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix

from utils import code_path


app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploaded_files"
app.config["EXPLANATIONS"] = "explanations.json"
app.secret_key = "super secret key"

Talisman(app, content_security_policy=None,
         strict_transport_security=False, force_https=False)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)


@app.route("/")
def default_path():
    return redirect("editor", code=302)


@app.route("/editor", methods=["GET"])
def editor():
    return render_template("editor.html")


@app.route("/editor/code/umime_count_a", methods=["GET"])
def editor_example_umime():
    return redirect(url_for(
        "editor_code",
        code_hash="c4bc51f7d34f9340c33e0b3b9dcfd12aa8917fe5a11faa5f6385f5bb41be9fcf",
    ))


@app.route("/editor/code/<string:code_hash>", methods=["GET"])
def editor_code(code_hash: str):
    with open(code_path(app.config["UPLOAD_FOLDER"], code_hash)) as f:
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
