# -*- coding: utf-8 -*-
from app import create_app
from models import db
import sys
import io

# Configura encoding para UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = create_app()

with app.app_context():
    db.create_all()
    print("Banco de dados inicializado com sucesso!")
    print("Tabelas criadas no MySQL: produto, usuario_info, avaliacao")
