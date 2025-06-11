from db import get_connection

def popular_tabelas_fixas():
    conn = get_connection()
    cursor = conn.cursor()

    # Verifica se já existem entradas
    cursor.execute("SELECT COUNT(*) FROM tipo_tabela_progressiva")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO tipo_tabela_progressiva (id_tipo, descricao)
            VALUES (?, ?)
        """, [
            (1, 'tabela progressiva IR'),
            (2, 'tabela ganho capital')
        ])

    cursor.execute("SELECT COUNT(*) FROM tipo_entrada")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO tipo_entrada (
                id_tipo, descricao_tipo, incide_ir, tipo_tabela_progressiva,
                imposto_alternativo, porcentagem_imposto_alternativo
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            (1, 'Salário (CLT)', True, 1, None, None),
            (2, 'Aposentadoria', True, 1, None, None),
            (3, 'Aluguéis', True, 1, None, None),
            (4, 'Rendimentos não tributáveis', False, 1, None, None),
            (5, 'Venda de imóveis', False, None, 'ITBI', 3.2),
            (6, 'Venda de bens móveis', False, None, '', 5.0),
            (7, 'Recebimento de doação', False, None, 'Doação', 4.0),
            (8, 'Recebimento de herança', False, None, 'Herança', 0.0),
            (9, 'Ganho de capital em operações de compra e venda', True, 2, None, None),
            (10, 'Participação majoritária em Offshore', True, 1, None, None),
            (11, 'Rendimento no exterior', True, 1, None, None)
        ])

    conn.commit()
    conn.close()
