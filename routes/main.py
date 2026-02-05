from flask import Blueprint, render_template, redirect, url_for, session
from models import Produto, UsuarioInfo, Avaliacao, db
from sqlalchemy import func
from utils import is_admin_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    try:
        # Otimização: Buscar todas as estatísticas em consultas mais eficientes
        # Usar cache de contagem se disponível, ou consultas otimizadas
        total_usuarios = db.session.query(func.count(UsuarioInfo.id)).scalar() or 0
        total_produtos = db.session.query(func.count(Produto.id)).scalar() or 0
        
        # Buscar contagens de produtos por tipo em uma única consulta
        produtos_stats = db.session.query(
            Produto.tipo,
            func.count(Produto.id)
        ).filter_by(status='disponivel').group_by(Produto.tipo).all()
        
        produtos_venda = 0
        produtos_troca = 0
        for tipo, count in produtos_stats:
            if tipo == 'venda':
                produtos_venda = count
            elif tipo == 'troca':
                produtos_troca = count
    except Exception as e:
        # Se houver erro (banco não inicializado), usar valores padrão
        print(f"Erro ao buscar estatísticas: {e}")
        total_usuarios = 0
        total_produtos = 0
        produtos_venda = 0
        produtos_troca = 0
    
    return render_template(
        'index.html',
        total_usuarios=total_usuarios,
        total_produtos=total_produtos,
        produtos_venda=produtos_venda,
        produtos_troca=produtos_troca
    )

@main_bp.route('/home')
def home():
    if not session.get('usuario_logado'):
        return redirect(url_for('auth.login'))
    
    # Buscar produtos disponíveis
    produtos = Produto.query.filter_by(status='disponivel').all()
    dados_usuario = session.get('dados_usuario', {})
    
    # Produtos com localização para o mapa
    produtos_com_localizacao = [p for p in produtos if p.latitude and p.longitude]
    
    # Otimização: Buscar todas as avaliações de uma vez usando subquery/agregação
    produto_ids = [p.id for p in produtos]
    
    if produto_ids:
        # Buscar todas as avaliações de uma vez
        avaliacoes_data = db.session.query(
            Avaliacao.produto_id,
            func.count(Avaliacao.id).label('total'),
            func.avg(Avaliacao.nota).label('media')
        ).filter(Avaliacao.produto_id.in_(produto_ids)).group_by(Avaliacao.produto_id).all()
        
        # Criar dicionário para acesso rápido
        avaliacoes_dict = {prod_id: {'total': total, 'media': round(float(media), 1)} 
                          for prod_id, total, media in avaliacoes_data}
    else:
        avaliacoes_dict = {}
    
    # Montar lista de produtos com avaliações
    produtos_com_avaliacoes = []
    for produto in produtos:
        aval_info = avaliacoes_dict.get(produto.id, {'total': 0, 'media': 0})
        produtos_com_avaliacoes.append({
            'produto': produto,
            'media_avaliacao': aval_info['media'],
            'total_avaliacoes': aval_info['total']
        })
    
    return render_template(
        'home.html',
        produtos=produtos,
        produtos_com_avaliacoes=produtos_com_avaliacoes,
        produtos_mapa=produtos_com_localizacao,
        usuario=dados_usuario,
        is_admin=is_admin_user(),
        pode_criar=session.get('usuario_logado', False)
    )

