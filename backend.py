import flask # type: ignore
import sqlite3
import os
from datetime import datetime

app = flask.Flask(__name__)
DB_NAME = "eventos.db"

def init_db():
    """Inicializa o banco de dados SQLite"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL,
            evento TEXT NOT NULL,
            data_inscricao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'confirmado'
        )
    ''')
    
    # Adicionar coluna data_solicitacao se não existir (para bancos antigos)
    try:
        cursor.execute("ALTER TABLE participantes ADD COLUMN data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass  # Coluna já existe
    
    conn.commit()
    conn.close()

# Garantir que o banco existe ao importar
init_db()

def get_db_connection():
    """Obtém conexão com o banco de dados"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Rota principal - renderiza o HTML"""
    return flask.render_template('index.html')

@app.route('/api/participantes', methods=['GET'])
def listar_participantes():
    """Retorna lista de participantes confirmados e lista de espera"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total de vagas
    vagas_totais = 10
    
    # Contar confirmados e lista de espera
    cursor.execute("SELECT COUNT(*) as total FROM participantes WHERE status = 'confirmado'")
    total_confirmados = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) as total FROM participantes WHERE status = 'espera'")
    total_espera = cursor.fetchone()[0]
    
    vagas_disponiveis = vagas_totais - total_confirmados
    
    # Listar confirmados
    cursor.execute("""
        SELECT id, nome, email, telefone, evento, data_inscricao
        FROM participantes 
        WHERE status = 'confirmado'
        ORDER BY data_inscricao ASC
    """)
    confirmados = [dict(row) for row in cursor.fetchall()]
    
    # Listar lista de espera
    cursor.execute("""
        SELECT id, nome, email, telefone, evento, data_inscricao
        FROM participantes 
        WHERE status = 'espera'
        ORDER BY data_inscricao ASC
    """)
    lista_espera = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    # Mapear nomes de eventos
    eventos_nomes = {
        'workshop': 'Workshop de Programação',
        'palestra': 'Palestra de Tecnologia',
        'curso': 'Curso de Python'
    }
    
    for p in confirmados:
        p['evento_nome'] = eventos_nomes.get(p['evento'], p['evento'])
    
    for p in lista_espera:
        p['evento_nome'] = eventos_nomes.get(p['evento'], p['evento'])
        p['data_solicitacao'] = p['data_inscricao']
    
    return flask.jsonify({
        'vagas_totais': vagas_totais,
        'vagas_disponiveis': max(0, vagas_disponiveis),
        'total_confirmados': total_confirmados,
        'total_espera': total_espera,
        'confirmados': confirmados,
        'lista_espera': lista_espera
    })

@app.route('/api/inscricao', methods=['POST'])
def realizar_inscricao():
    """Realiza a inscrição de um participante"""
    data = flask.request.get_json()
    
    nome = data.get('nome', '').strip()
    email = data.get('email', '').strip()
    telefone = data.get('telefone', '').strip()
    evento = data.get('evento', '').strip()
    
    # Validações
    if not nome or not email or not telefone or not evento:
        return flask.jsonify({'erro': 'Todos os campos são obrigatórios'}), 400
    
    # Verificar se email já está cadastrado
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM participantes WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return flask.jsonify({'erro': 'Este e-mail já está cadastrado'}), 400
    
    # Verificar vagas disponíveis
    vagas_totais = 10
    cursor.execute("SELECT COUNT(*) as total FROM participantes WHERE status = 'confirmado'")
    total_confirmados = cursor.fetchone()[0]
    
    if total_confirmados < vagas_totais:
        status = 'confirmado'
        # Gerar número de inscrição
        cursor.execute("SELECT MAX(id) FROM participantes WHERE status = 'confirmado'")
        max_id = cursor.fetchone()[0] or 0
        num_inscricao = f"INS{str(max_id + 1).zfill(4)}"
    else:
        status = 'espera'
        # Posição na lista de espera
        cursor.execute("SELECT COUNT(*) FROM participantes WHERE status = 'espera'")
        posicao = cursor.fetchone()[0] + 1
        num_inscricao = f"ESP{str(posicao).zfill(4)}"
    
    # Inserir participante
    cursor.execute("""
        INSERT INTO participantes (nome, email, telefone, evento, status)
        VALUES (?, ?, ?, ?, ?)
    """, (nome, email, telefone, evento, status))
    
    participante_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Mapear nome do evento
    eventos_nomes = {
        'workshop': 'Workshop de Programação',
        'palestra': 'Palestra de Tecnologia',
        'curso': 'Curso de Python'
    }
    
    return flask.jsonify({
        'status': status,
        'participante': {
            'id': num_inscricao,
            'nome': nome,
            'email': email,
            'telefone': telefone,
            'evento': eventos_nomes.get(evento, evento)
        },
        'posicao': posicao if status == 'espera' else None
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
