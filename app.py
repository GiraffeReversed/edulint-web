from flask import Flask, redirect, url_for
from flask_talisman import Talisman
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import toml
import json
from markdown import markdown

from api import bp as api_bp, get_explanations
from utils import explanations_path, Version, cache, cache_config


app = Flask(__name__)
app.config.from_file("config.toml", load=toml.load)
app.config["VERSIONS"] = [Version(v) for v in app.config["VERSIONS"]]

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
csp["connect-src"] = csp["default-src"] + ["https://edulint.com", "https://edulint.rechtackova.cz"]

cors = CORS(app)

Talisman(app, content_security_policy=csp, strict_transport_security=False, force_https=False)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)


@app.route("/", methods=["GET"])
def redirect_to_real_swagger():
    return redirect(url_for("api.get_swagger"))


def prepare_HTML_explanations(app):
    exps = get_explanations()

    HTML_exps = {
        code: {key: markdown(exps[code][key], extensions=["fenced_code", "codehilite"]) for key in exps[code]}
        for code in exps
    }

    with open(explanations_path(app.config), "w") as f:
        f.write(json.dumps(HTML_exps))


with app.app_context():
    prepare_HTML_explanations(app)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
