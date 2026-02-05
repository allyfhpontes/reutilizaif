import requests
from flask import session
from config import Config
from models import UsuarioInfo

def autenticar_suap(matricula, senha):
    """Autentica usuário no SUAP e retorna dados"""
    try:
        # Endpoints conforme documentação: https://suap.ifrn.edu.br/api/docs/
        # Endpoint correto: /api/token/pair (sem v2, conforme documentação oficial)
        endpoints = [
            f"{Config.SUAP_API_BASE_URL}/api/token/pair",  # Endpoint oficial conforme documentação
        ]
        
        data = {
            'username': str(matricula).strip(),
            'password': str(senha).strip()
        }
        
        headers_json = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        response = None
        last_error = None
        
        for url in endpoints:
            try:
                # Tenta primeiro com JSON (formato correto conforme api.json)
                response = requests.post(
                    url, 
                    json=data, 
                    headers=headers_json, 
                    timeout=15,  # Aumentado para 15 segundos
                    allow_redirects=False,
                    verify=True  # Verifica certificado SSL
                )
                
                if response.status_code in [200, 201]:
                    print(f"✓ Sucesso com endpoint: {url}")  # Debug
                    break
                elif response.status_code == 401:
                    # Credenciais inválidas - não tenta outros endpoints
                    last_error = f"HTTP {response.status_code}"
                    print(f"✗ {url} retornou 401 (credenciais inválidas)")
                    break
                elif response.status_code == 404:
                    # Endpoint não existe - continua para próximo
                    print(f"✗ {url} retornou 404 (endpoint não existe)")
                    last_error = f"HTTP {response.status_code}"
                    continue
                else:
                    # Outro erro - tenta form-data como fallback
                    print(f"✗ {url} retornou {response.status_code}, tentando form-data...")
                    try:
                        response_form = requests.post(
                            url, 
                            data=data, 
                            timeout=15,
                            allow_redirects=False,
                            verify=True
                        )
                        
                        if response_form.status_code in [200, 201]:
                            response = response_form
                            print(f"✓ Sucesso com endpoint (form-data): {url}")  # Debug
                            break
                        else:
                            last_error = f"HTTP {response.status_code}"
                            print(f"✗ {url} (form-data) retornou {response_form.status_code}: {response_form.text[:200]}")
                    except:
                        last_error = f"HTTP {response.status_code}"
                        
            except requests.exceptions.ConnectionError as e:
                last_error = f"ConnectionError: Não foi possível conectar ao servidor"
                print(f"✗ Erro de conexão com {url}: {str(e)[:100]}")
                continue
            except requests.exceptions.Timeout as e:
                last_error = f"Timeout: Servidor demorou muito para responder"
                print(f"✗ Timeout com {url}")
                continue
            except requests.exceptions.SSLError as e:
                last_error = f"SSLError: Problema com certificado SSL"
                print(f"✗ Erro SSL com {url}: {str(e)[:100]}")
                continue
            except requests.exceptions.RequestException as e:
                last_error = f"{type(e).__name__}: {str(e)[:150]}"
                print(f"✗ Erro de requisição com {url}: {last_error}")
                continue
            except Exception as e:
                last_error = f"{type(e).__name__}: {str(e)[:150]}"
                print(f"✗ Erro inesperado com {url}: {last_error}")
                continue
        
        if not response:
            # Mensagem de erro mais informativa
            if last_error:
                if 'ConnectionError' in last_error or 'ConnectTimeout' in last_error:
                    erro_msg = 'Não foi possível conectar ao servidor SUAP. Verifique sua conexão com a internet.'
                elif 'Timeout' in last_error:
                    erro_msg = 'O servidor SUAP demorou muito para responder. Tente novamente.'
                elif 'SSLError' in last_error:
                    erro_msg = 'Erro de certificado SSL. Verifique sua conexão.'
                else:
                    erro_msg = f'Erro ao conectar: {last_error}'
            else:
                erro_msg = 'Não foi possível conectar ao SUAP. Verifique sua conexão e tente novamente.'
            
            return {
                'sucesso': False,
                'erro': erro_msg
            }
        
        if response.status_code in [200, 201]:
            try:
                token_data = response.json()
                # Conforme api.json, o endpoint retorna 'access' e 'refresh'
                token = token_data.get('access') or token_data.get('token') or token_data.get('access_token')
                refresh_token = token_data.get('refresh')  # Salvar refresh token para uso futuro
                
                if token:
                    user_info = obter_dados_usuario_suap(token)
                    
                    if user_info:
                        vinculo = user_info.get('vinculo', {})
                        tipo_vinculo = str(user_info.get('tipo_vinculo', '')).lower()
                        
                        is_aluno = False
                        
                        if tipo_vinculo:
                            if ('aluno' in tipo_vinculo or 
                                'estudante' in tipo_vinculo or
                                'student' in tipo_vinculo or
                                tipo_vinculo == 'aluno' or
                                tipo_vinculo == 'estudante'):
                                
                                if isinstance(vinculo, dict):
                                    situacao = str(vinculo.get('situacao', '')).lower()
                                    situacoes_inativas = ['inativo', 'cancelado', 'trancado', 'desligado', 'concluído']
                                    if situacao and not any(sit in situacao for sit in situacoes_inativas):
                                        is_aluno = True
                                    elif not situacao:
                                        is_aluno = True
                                else:
                                    is_aluno = True
                        
                        if not is_aluno and isinstance(vinculo, dict):
                            if vinculo.get('curso') or vinculo.get('campus'):
                                situacao = str(vinculo.get('situacao', '')).lower()
                                situacoes_inativas = ['inativo', 'cancelado', 'trancado', 'desligado', 'concluído']
                                if not situacao or not any(sit in situacao for sit in situacoes_inativas):
                                    is_aluno = True
                        
                        if not is_aluno:
                            is_aluno = True  # Permitir acesso mesmo sem identificação clara
                        
                        return {
                            'sucesso': True,
                            'token': token,
                            'dados_usuario': user_info,
                            'is_aluno': is_aluno
                        }
                    else:
                        return {
                            'sucesso': False,
                            'erro': 'Não foi possível obter os dados do usuário'
                        }
                else:
                    return {
                        'sucesso': False,
                        'erro': 'Token não encontrado na resposta do SUAP'
                    }
            except ValueError as e:
                return {
                    'sucesso': False,
                    'erro': f'Resposta inválida do SUAP: {str(e)}'
                }
        elif response.status_code == 401:
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', 'Credenciais inválidas')
                return {
                    'sucesso': False,
                    'erro': error_detail
                }
            except:
                return {
                    'sucesso': False,
                    'erro': 'Credenciais inválidas. Verifique sua matrícula e senha.'
                }
        else:
            error_msg = 'Erro ao autenticar'
            try:
                error_data = response.json()
                error_msg = error_data.get('detail') or error_data.get('message') or error_data.get('error') or error_msg
            except:
                error_text = response.text[:500] if response.text else 'Sem resposta'
                error_msg = f'Erro {response.status_code}: {error_text}'
            
            return {
                'sucesso': False,
                'erro': error_msg
            }
            
    except requests.exceptions.Timeout:
        return {
            'sucesso': False,
            'erro': 'Timeout ao conectar com o SUAP. Tente novamente.'
        }
    except requests.exceptions.RequestException as e:
        return {
            'sucesso': False,
            'erro': f'Erro ao conectar com o SUAP: {str(e)}'
        }
    except Exception as e:
        return {
            'sucesso': False,
            'erro': f'Erro inesperado: {str(e)}'
        }


def obter_dados_usuario_suap(token):
    """Obtém dados do usuário do SUAP usando o token"""
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        # Endpoints conforme documentação: https://suap.ifrn.edu.br/api/docs
        # Priorizando /api/rh/eu/ que retorna dados pessoais completos (nome_social, nome_usual, nome_registro, nome, etc)
        endpoints_dados = [
            f"{Config.SUAP_API_BASE_URL}/api/rh/eu/",  # Endpoint principal - retorna dados pessoais completos
            f"{Config.SUAP_API_BASE_URL}/api/ensino/meus-dados-aluno/",  # Endpoint específico para alunos
            f"{Config.SUAP_API_BASE_URL}/api/rh/meus-dados/",  # Endpoint geral
            f"{Config.SUAP_API_BASE_URL}/api/v2/rh/eu/",  # Fallback v2
            f"{Config.SUAP_API_BASE_URL}/api/v2/ensino/meus-dados-aluno/",  # Fallback v2
            f"{Config.SUAP_API_BASE_URL}/api/v2/rh/meus-dados/",  # Fallback v2
        ]
        
        dados = None
        last_error_dados = None
        for url in endpoints_dados:
            try:
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=15,
                    verify=True
                )
                
                if response.status_code == 200:
                    dados = response.json()
                    print(f"✓ Dados obtidos com sucesso de: {url}")  # Debug
                    break
                else:
                    print(f"✗ {url} retornou {response.status_code}: {response.text[:200]}")  # Debug
                    last_error_dados = f"HTTP {response.status_code}"
                    
            except requests.exceptions.ConnectionError as e:
                last_error_dados = f"ConnectionError: {str(e)[:100]}"
                print(f"✗ Erro de conexão com {url}: {last_error_dados}")
                continue
            except requests.exceptions.Timeout as e:
                last_error_dados = "Timeout ao obter dados"
                print(f"✗ Timeout com {url}")
                continue
            except Exception as e:
                last_error_dados = f"{type(e).__name__}: {str(e)[:150]}"
                print(f"✗ Erro com {url}: {last_error_dados}")
                continue
        
        if dados:
            # Normaliza nome - API SUAP /api/rh/eu/ retorna: nome_social, nome_usual, nome_registro, nome, primeiro_nome, ultimo_nome
            # Prioridade conforme documentação: nome_usual > nome_social > nome > nome_registro > primeiro_nome + ultimo_nome
            nome = (dados.get('nome_usual') or 
                   dados.get('nome_social') or 
                   dados.get('nome') or 
                   dados.get('nome_registro') or
                   (dados.get('primeiro_nome', '') + ' ' + dados.get('ultimo_nome', '')).strip() or
                   '')
            if nome:
                dados['nome_usual'] = nome
                dados['nome'] = nome
                # Preserva nome_social se existir
                if dados.get('nome_social') and not dados.get('nome_social') == nome:
                    dados['nome_social'] = dados.get('nome_social')
            
            # Normaliza foto
            if 'foto' in dados and dados['foto']:
                foto = dados['foto']
                if foto.startswith('/'):
                    dados['foto'] = f"https://suap.ifrn.edu.br{foto}"
                elif not foto.startswith('http'):
                    dados['foto'] = f"https://suap.ifrn.edu.br{foto}"
            elif 'url_foto' in dados and dados['url_foto']:
                dados['foto'] = dados['url_foto']
            elif 'foto_150x200' in dados and dados['foto_150x200']:
                dados['foto'] = dados['foto_150x200']
            elif 'url_foto_150x200' in dados and dados['url_foto_150x200']:
                dados['foto'] = dados['url_foto_150x200']
            
            # Normaliza vínculos (pode vir como 'vinculo' singular ou 'vinculos' plural)
            vinculos = dados.get('vinculos') or []
            if not vinculos and 'vinculo' in dados:
                vinculo = dados['vinculo']
                if isinstance(vinculo, dict):
                    vinculos = [vinculo]
                elif isinstance(vinculo, list):
                    vinculos = vinculo
            
            if vinculos:
                dados['vinculos'] = vinculos
                for vinculo in vinculos:
                    if isinstance(vinculo, dict):
                        # Extrai nome do curso
                        if 'curso' in vinculo and isinstance(vinculo['curso'], dict):
                            curso_nome = vinculo['curso'].get('nome', '')
                            if curso_nome:
                                vinculo['curso_nome'] = curso_nome
                        
                        # Extrai nome do campus
                        if 'campus' in vinculo and isinstance(vinculo['campus'], dict):
                            campus_nome = vinculo['campus'].get('nome', '')
                            if campus_nome:
                                vinculo['campus_nome'] = campus_nome
            
            # Se não tem vínculos mas tem curso/campus direto
            if not vinculos:
                if 'curso' in dados and isinstance(dados['curso'], dict):
                    dados['curso_nome'] = dados['curso'].get('nome', '')
                if 'campus' in dados and isinstance(dados['campus'], dict):
                    dados['campus_nome'] = dados['campus'].get('nome', '')
            
            return dados
        
        # Se não conseguiu obter dados, loga o erro
        print(f"✗ Não foi possível obter dados do usuário. Último erro: {last_error_dados}")
        return None
            
    except Exception as e:
        print(f"Erro ao obter dados do usuário: {str(e)}")
        return None


def salvar_info_usuario(db_session, matricula, dados_usuario):
    """Salva informações do usuário no banco de dados"""
    from models import UsuarioInfo
    
    if not matricula:
        return

    info = UsuarioInfo.query.filter_by(matricula=matricula).first()
    if not info:
        info = UsuarioInfo(matricula=matricula)
        db_session.session.add(info)

    # Coleta nome - API /api/rh/eu/ retorna: nome_social, nome_usual, nome_registro, nome, primeiro_nome, ultimo_nome
    # Prioridade: nome_usual > nome_social > nome > nome_registro > primeiro_nome + ultimo_nome
    nome = (dados_usuario.get('nome_usual') or 
           dados_usuario.get('nome_social') or 
           dados_usuario.get('nome') or 
           dados_usuario.get('nome_registro') or
           (dados_usuario.get('primeiro_nome', '') + ' ' + dados_usuario.get('ultimo_nome', '')).strip() or
           None)
    
    if nome:
        info.nome = nome

    vinculo = dados_usuario.get('vinculo') or {}
    curso = None
    campus = None
    if isinstance(vinculo, dict):
        curso = vinculo.get('curso')
        if isinstance(curso, dict):
            curso = curso.get('nome')
        campus = vinculo.get('campus')
        if isinstance(campus, dict):
            campus = campus.get('nome')

    if curso:
        info.curso = curso
    if campus:
        info.campus = campus

    foto = dados_usuario.get('url_foto_150x200') or dados_usuario.get('url_foto_75x100') or dados_usuario.get('foto')
    if foto:
        info.foto_url = foto

    db_session.session.commit()


def is_admin_user():
    """Retorna True se o usuário na sessão é admin (config ou is_admin no banco)."""
    matricula = session.get('matricula')
    if not matricula:
        return False
    if matricula in Config.ADMIN_MATRICULAS:
        return True
    u = UsuarioInfo.query.filter_by(matricula=matricula).first()
    return bool(u and getattr(u, 'is_admin', False))
