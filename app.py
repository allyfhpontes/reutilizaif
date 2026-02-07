from flask import Flask
from config import Config
from models import db
from routes.auth import auth_bp
from routes.main import main_bp
from routes.produtos import produtos_bp
from routes.perfil import perfil_bp
from routes.admin import admin_bp

#def create_app():
    #app = Flask(__name__)
def create_app():
    app = Flask(_name_)
    return app
 app.config.from_object(Config)
 app = create_app()
   
   
app = create_app()
    
    # Inicializa extensões
    db.init_app(app)
    
    # Registra blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(produtos_bp)
    app.register_blueprint(perfil_bp)
    app.register_blueprint(admin_bp)
    
    # Context processor: is_admin disponível em todos os templates
    @app.context_processor
    def inject_admin():
        from utils import is_admin_user
        return dict(is_admin=is_admin_user())
    
    # Cria tabelas e aplica migrações pendentes (ex.: coluna is_admin)
    with app.app_context():
        db.create_all()
        _migrate_is_admin_if_needed(app)
    
    return app


def _migrate_is_admin_if_needed(app):
    """Adiciona coluna is_admin em usuario_info se o banco já existia antes da área admin."""
    from sqlalchemy import text
    uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if 'sqlite' not in uri.lower():
        return
    with app.app_context():
        with db.engine.connect() as conn:
            r = conn.execute(text("PRAGMA table_info(usuario_info)"))
            cols = [row[1] for row in r.fetchall()]
            if 'is_admin' not in cols:
                conn.execute(text("ALTER TABLE usuario_info ADD COLUMN is_admin INTEGER DEFAULT 0"))
                conn.commit()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
