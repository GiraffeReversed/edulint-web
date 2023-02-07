from flask import Flask
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix
import toml
from markdown import markdown
import json

from web import bp as web_bp
from api import bp as api_bp, with_version

from utils import get_latest, explanations_path, Version, cache, cache_config


app = Flask(__name__)
app.config.from_file("config.toml", load=toml.load)
app.config["VERSIONS"] = [Version(v) for v in app.config["VERSIONS"]]

app.config.from_mapping(cache_config)
cache.init_app(app)

app.secret_key = "super secret key"
app.register_blueprint(web_bp)
app.register_blueprint(api_bp)

csp = {
    'default-src': [
        "'self'",
        "data:",
        "https://cdnjs.cloudflare.com",
        "https://cdn.jsdelivr.net",
        "https://plaus.borysek.eu",
    ],
}
csp['style-src'] = csp['default-src'] + ["'unsafe-inline'"]

Talisman(app, content_security_policy=csp,
         strict_transport_security=False, force_https=False)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)


def get_explanations():
    from edulint.explanations import get_explanations

    return get_explanations()


@app.before_first_request
def prepare_HTML_explanations():
    exps = with_version(get_latest(app.config["VERSIONS"]), get_explanations)

    HTML_exps = {
        code: {
            key: markdown(
                exps[code][key], extensions=["fenced_code", "codehilite"]) for key in exps[code]
        } for code in exps
    }

    with open(explanations_path(app.config), "w") as f:
        f.write(json.dumps(HTML_exps))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
