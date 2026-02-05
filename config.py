import os
from os.path import join, dirname
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    USE_SQLITE = os.environ.get('USE_SQLITE', '').lower() in ('1', 'true', 'yes')
    
    if USE_SQLITE:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///reutilizaif.db'
    else:
        MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
        MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
        MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''
        MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'reutilizaif'
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}"
        )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API SUAP
    # Base URL conforme documentação: https://suap.ifrn.edu.br/api/docs/
    SUAP_API_BASE_URL = "https://suap.ifrn.edu.br"
    # Matrículas iniciais de admin (configurável por env, separadas por vírgula)
    _admin_raw = os.environ.get('ADMIN_MATRICULAS', '20231041110013,20221041110028')
    ADMIN_MATRICULAS = {m.strip() for m in _admin_raw.split(',') if m.strip()}

