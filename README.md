# ReutilizaIF

Projeto web Flask para reutilização de itens (produtos) no âmbito do IFRN.

---

## Pré-requisitos

- **Python 3.11** (ou 3.10+)
- **MySQL** (apenas se for usar MySQL; para desenvolvimento sem MySQL, use SQLite — veja abaixo)
- **Git** (opcional, para clonar o repositório)

---

## Como rodar o projeto

### 1. Clonar ou acessar o projeto

Se você tiver o repositório no GitHub:

```bash
git clone https://github.com/reutilizaIF.git
cd reutilizaIF
```

Ou acesse a pasta do projeto no seu computador e abra o terminal nela.

---

### 2. Criar o ambiente virtual (venv)

Na pasta raiz do projeto, crie o ambiente virtual:

```bash
python3 -m venv venv
```

No Windows, se o comando acima não funcionar, tente:

```bash
py -3 -m venv venv
```

---

### 3. Ativar o ambiente virtual

**Linux e macOS:**

```bash
. venv/bin/activate
```

**Windows (PowerShell):**

```powershell
venv\Scripts\Activate.ps1
```

**Windows (CMD):**

```cmd
venv\Scripts\activate.bat
```

Quando o venv estiver ativo, o prompt deve mostrar algo como `(venv)` no início da linha.

---

### 4. Instalar as dependências

Com o venv ativado:

```bash
pip install -r requirements.txt
```

---

### 5. Configurar o arquivo `.env`

Copie o arquivo de exemplo e edite com seus dados:

```bash
cp env.example .env
```

**Rodar sem MySQL (desenvolvimento local):**  
O `env.example` já vem com `USE_SQLITE=1`. Assim o projeto usa **SQLite** e não precisa de MySQL. O arquivo do banco será criado na raiz do projeto (`reutilizaif.db`).

**Rodar com MySQL:**  
No `.env`, defina `USE_SQLITE=0` (ou apague a linha) e preencha:

- `MYSQL_HOST` – host do MySQL (ex.: `localhost`)
- `MYSQL_USER` – usuário do MySQL
- `MYSQL_PASSWORD` – senha do MySQL
- `MYSQL_DATABASE` – nome do banco (ex.: `reutilizaif`)
- `SECRET_KEY` – chave secreta da aplicação (troque em produção)

Crie o banco no MySQL com o mesmo nome definido em `MYSQL_DATABASE`, se ainda não existir.

---

### 6. (Opcional) Inicializar o banco de dados

As tabelas são criadas automaticamente na primeira execução do `app.py`. Se quiser apenas criar as tabelas antes:

```bash
python init_db.py
```

---

### 7. Rodar o projeto

Com o venv ativado e o `.env` configurado:

```bash
python app.py
```

A aplicação sobe em modo de desenvolvimento em:

**http://localhost:5000**

Abra esse endereço no navegador para acessar o ReutilizaIF.

---

## Resumo rápido (já com o projeto na pasta)

```bash
# Criar e ativar o venv (Linux/macOS)
python3 -m venv venv
. venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar ambiente (copiar e editar .env)
cp env.example .env

# Rodar
python app.py
```

---

## Desativar o ambiente virtual

Quando terminar de trabalhar no projeto:

```bash
deactivate
```

O `(venv)` some do prompt e você volta ao ambiente global do Python.

---

## Erro "Connection refused" ao MySQL

Se aparecer **"Can't connect to MySQL server on 'localhost' (Connection refused)"**:

1. **Usar SQLite em desenvolvimento:** no `.env`, deixe ou defina `USE_SQLITE=1`. O projeto usará SQLite e não precisará de MySQL.
2. **Ou instalar e subir o MySQL:** instale o MySQL no sistema, crie o banco, configure o `.env` com `USE_SQLITE=0` e os dados do MySQL.

---

## Área administrativa

Usuários com permissão de **admin** podem:

- **Usuários:** ver todos os usuários e **dar ou remover permissão de admin** para qualquer usuário.
- **Produtos:** ver todos os produtos, **editar** e **excluir** qualquer produto.

Quem é admin:

- Matrículas definidas em `ADMIN_MATRICULAS` no `.env` (separadas por vírgula) ou o padrão em `config.py`.
- Qualquer usuário que um admin tenha marcado como admin na tela **Admin → Usuários**.

Se você já tinha o banco antes da área admin, adicione a coluna `is_admin`:

- **SQLite:** `sqlite3 reutilizaif.db "ALTER TABLE usuario_info ADD COLUMN is_admin INTEGER DEFAULT 0;"`
- **MySQL:** `ALTER TABLE usuario_info ADD COLUMN is_admin TINYINT(1) DEFAULT 0;`
