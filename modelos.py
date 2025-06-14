from db import get_connection

def criar_tabelas():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS usuario (
        cpf TEXT PRIMARY KEY,
        nome_completo TEXT NOT NULL,
        idade INTEGER NOT NULL,
        profissao TEXT
    );

    CREATE TABLE IF NOT EXISTS dependente (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cpf_usuario TEXT NOT NULL,
        nome_completo TEXT NOT NULL,
        FOREIGN KEY (cpf_usuario) REFERENCES usuario(cpf) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS tipo_tabela_progressiva (
        id_tipo INTEGER PRIMARY KEY,
        descricao TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tipo_entrada (
        id_tipo INTEGER PRIMARY KEY,
        descricao_tipo TEXT NOT NULL,
        incide_ir BOOLEAN NOT NULL,
        tipo_tabela_progressiva INTEGER,
        tem_deducao_tabela_progressiva BOOLEAN NOT NULL,
        imposto_alternativo TEXT,
        porcentagem_imposto_alternativo REAL,
        FOREIGN KEY (tipo_tabela_progressiva) REFERENCES tipo_tabela_progressiva(id_tipo)
    );

    CREATE TABLE IF NOT EXISTS entrada_mensal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cpf_usuario TEXT NOT NULL,
        data_entrada TEXT NOT NULL,
        id_tipo_entrada INTEGER NOT NULL,
        valor REAL NOT NULL,
        valor_desconto REAL NOT NULL,
        descricao_desconto TEXT NOT NULL,
        FOREIGN KEY (cpf_usuario) REFERENCES usuario(cpf) ON DELETE CASCADE,
        FOREIGN KEY (id_tipo_entrada) REFERENCES tipo_entrada(id_tipo)
    );
        
    CREATE TABLE IF NOT EXISTS tabela_progressiva (
        id_tabela_progressiva INTEGER NOT NULL,
        valor_superior_faixa REAL NOT NULL,
        aliquota REAL NOT NULL,
        deducao REAL NOT NULL,
        idade_deducao_adicional INT,
        deducao_adicional REAL,
        PRIMARY KEY (id_tabela_progressiva, valor_superior_faixa)
    );
        
    """)

    conn.commit()
    conn.close()
