import os
from flask import Flask, redirect, url_for
from app.config import Config
from app.routes.excel_upload import excel_upload_bp
from app.routes.asp import asp_bp
from app.routes.admin import admin_bp


def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    # Ensure runtime directories exist
    os.makedirs(app.config["UPLOAD_FOLDER"],       exist_ok=True)  # files/upload/
    os.makedirs(app.config["EXCEL_UPLOAD_FOLDER"], exist_ok=True)  # files/upload/excel/
    os.makedirs(app.config["EXCELS_DIR"],          exist_ok=True)  # files/download/excel/

    # Register blueprints
    app.register_blueprint(excel_upload_bp)  # legacy: /upload-excel (kept for backward compat)
    app.register_blueprint(asp_bp)           # /asp/*
    app.register_blueprint(admin_bp)         # /admin/*

    # Root → ASP dashboard
    @app.route("/")
    def root():
        return redirect(url_for("asp.dashboard"))

    return app
