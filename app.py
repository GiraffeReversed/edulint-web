from flask import Flask, redirect, url_for, request
from flask_talisman import Talisman
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import toml
import json
import os
import tracemalloc
from markdown import markdown

from api import bp as api_bp, get_explanations
from utils import explanations_path, cache, cache_config
from database_management import prepare_db


app = Flask(__name__)
app.config.from_file("config.toml", load=toml.load)

app.config.from_mapping(cache_config)
cache.init_app(app)

app.secret_key = "super secret key"
app.register_blueprint(api_bp)

csp = {
    "default-src": [
        "'self'",
        "data:",
        "https://cdnjs.cloudflare.com",
        "https://cdn.jsdelivr.net",
        "https://unpkg.com",
        "https://plaus.borysek.eu",
    ],
}
csp["style-src"] = csp["default-src"] + ["'unsafe-inline'"]
csp["connect-src"] = csp["default-src"] + [
    "https://edulint.com",
    "https://edulint.rechtackova.cz",
]

cors = CORS(app)

Talisman(
    app, content_security_policy=csp, strict_transport_security=False, force_https=False
)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)

memory_snapshot = None


@app.route("/api/memory_debug", methods=["GET"])
def memory_test():
    if os.environ.get("MEMORY_DEBUG_PASSWORD", None) is None:
        return "No password for memory debugging, the endpoint is disabled", 500
    if request.args.get("password", None) is None:
        return "Suply the password in query argument `password`", 401
    if os.environ["MEMORY_DEBUG_PASSWORD"] != request.args["password"]:
        return "Incorrect memory debug password", 401

    global memory_snapshot
    tracemalloc.start()
    if not memory_snapshot:
        memory_snapshot = (
            tracemalloc.take_snapshot()
        )  # Take a snapshot of the current memory usage
    else:
        top_stats = tracemalloc.take_snapshot().compare_to(memory_snapshot, "lineno")
        return "\n".join([str(x) for x in top_stats[:100]]), 200
    return "intial snapshot taken", "200"


@app.route("/", methods=["GET"])
def redirect_to_real_swagger():
    return redirect(url_for("api.get_swagger"))


def prepare_HTML_explanations(app):
    exps = get_explanations()

    HTML_exps = {
        code: {
            key: markdown(exps[code][key], extensions=["fenced_code", "codehilite"])
            for key in exps[code]
        }
        for code in exps
    }

    with open(explanations_path(app.config), "w") as f:
        f.write(json.dumps(HTML_exps))


with app.app_context():
    prepare_HTML_explanations(app)
    prepare_db()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
