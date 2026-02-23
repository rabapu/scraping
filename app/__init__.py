from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from config import Config
from app.models import User

csrf = CSRFProtect()
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Silakan login terlebih dahulu.'

    # Register blueprints
    from app.controllers.auth import auth_bp
    from app.controllers.keywords import keywords_bp
    from app.controllers.berita import berita_bp
    from app.controllers.tasks import tasks_bp
    from app.controllers.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(keywords_bp)
    app.register_blueprint(berita_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(users_bp)

    return app