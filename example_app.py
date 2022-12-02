from flask import Flask

from flask_profiler import init_app


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["FLASK_PROFILER"] = {
        "enabled": True,
    }

    @app.route("/")
    def hello_world():
        return "<p>Hello, World!</p>"

    init_app(app)
    return app


app = create_app()
