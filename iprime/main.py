
from flask import Flask

from config import Config
from models.db import init_db
from routes.auth_routes import auth_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Creates the users/email_otps tables in Neon if they don't exist yet.
    # Safe to run on every startup.
    init_db()

    app.register_blueprint(auth_bp)
    return app


app = create_app()

if __name__ == "__main__":
    # debug=True is for local development only — Render runs this via
    # gunicorn instead, which never has debug mode on.
    app.run(debug=True, port=5000)
