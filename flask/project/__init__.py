# init.py

import psycopg

from psycopg.rows import class_row
from flask import Flask
from flask_login import LoginManager 
from werkzeug.middleware.proxy_fix import ProxyFix


def create_app():
    app = Flask(__name__)

    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1
    )

    # CHANGE VALUE OF SECRET KEY ACCORDING TO:
    # https://flask.palletsprojects.com/en/3.0.x/quickstart/#sessions
    app.config['SECRET_KEY'] = 'ADMIN_KEY'

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        with psycopg.connect("host=db user=postgres password=admin") as conn:
            with conn.cursor(row_factory=class_row(User)) as cur:
                return cur.execute("SELECT * FROM users WHERE name = %s LIMIT 1", (user_id,)).fetchone()

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # blueprint for api routes in our app
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint)

    # blueprint for Nmap scan routes to be called from the web app
    from .NmapScan import scan as scan_blueprint
    app.register_blueprint(scan_blueprint)


    return app
