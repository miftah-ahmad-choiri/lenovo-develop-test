import os
from flask import Flask
from app.config import Config
from app.routes.ticket import ticket_bp
from app.routes.dashboard import dashboard_bp
from app.routes.excel_upload import excel_upload_bp


def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["EXCEL_UPLOAD_FOLDER"], exist_ok=True)

    app.register_blueprint(ticket_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(excel_upload_bp)

    return app
