import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
login_manager.login_message = 'Please log in to access this page.'


def create_app(config_name='default'):
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates'))
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    app.static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
    os.makedirs(app.config.get('UPLOAD_FOLDER_EQUIPMENT', app.static_folder + '/uploads/equipment'), exist_ok=True)
    os.makedirs(app.config.get('UPLOAD_FOLDER_AVATARS', app.static_folder + '/uploads/avatars'), exist_ok=True)
    os.makedirs(app.config.get('UPLOAD_FOLDER_INVOICES', app.static_folder + '/uploads/invoices'), exist_ok=True)

    from app.routes.auth import auth_bp
    from app.routes.farmer import farmer_bp
    from app.routes.owner import owner_bp
    from app.routes.admin import admin_bp
    from app.routes.payment import payment_bp
    from app.routes.reports import reports_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(farmer_bp)
    app.register_blueprint(owner_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)

    @app.context_processor
    def inject_helpers():
        from app.utils.helpers import format_currency, time_since
        return dict(format_currency=format_currency, time_since=time_since)

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    with app.app_context():
        db.create_all()

    return app
