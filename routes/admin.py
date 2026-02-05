from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, session, request
from models import db, UsuarioInfo, Produto, Avaliacao
from sqlalchemy import func
from utils import is_admin_user

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator: só permite acesso se o usuário for admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('usuario_logado'):
            return redirect(url_for('auth.login'))
        if not is_admin_user():
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@admin_required
def index():
    return redirect(url_for('admin.usuarios'))


@admin_bp.route('/usuarios')
@admin_required
def usuarios():
    usuarios_list = UsuarioInfo.query.order_by(UsuarioInfo.created_at.desc()).all()
    from config import Config
    # Marca quem é admin (config ou is_admin no banco)
    for u in usuarios_list:
        u._e_admin = (u.matricula in Config.ADMIN_MATRICULAS or getattr(u, 'is_admin', False))
    return render_template('admin/usuarios.html', usuarios=usuarios_list)


@admin_bp.route('/usuarios/<matricula>/toggle-admin', methods=['POST'])
@admin_required
def toggle_admin(matricula):
    usuario = UsuarioInfo.query.filter_by(matricula=matricula).first()
    if not usuario:
        return redirect(url_for('admin.usuarios'))
    usuario.is_admin = not getattr(usuario, 'is_admin', False)
    db.session.commit()
    return redirect(url_for('admin.usuarios'))


@admin_bp.route('/produtos')
@admin_required
def produtos():
    produtos_list = Produto.query.order_by(Produto.created_at.desc()).all()
    produto_ids = [p.id for p in produtos_list]
    if produto_ids:
        avaliacoes_data = db.session.query(
            Avaliacao.produto_id,
            func.count(Avaliacao.id).label('total'),
            func.avg(Avaliacao.nota).label('media')
        ).filter(Avaliacao.produto_id.in_(produto_ids)).group_by(Avaliacao.produto_id).all()
        avaliacoes_dict = {pid: {'total': total, 'media': round(float(media), 1)}
                           for pid, total, media in avaliacoes_data}
    else:
        avaliacoes_dict = {}
    produtos_com_avaliacoes = []
    for p in produtos_list:
        av = avaliacoes_dict.get(p.id, {'total': 0, 'media': 0})
        produtos_com_avaliacoes.append({'produto': p, 'media_avaliacao': av['media'], 'total_avaliacoes': av['total']})
    return render_template('admin/produtos.html', produtos_com_avaliacoes=produtos_com_avaliacoes)
