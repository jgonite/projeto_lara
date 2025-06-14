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
            (2, 'tabela progressiva IR aposentados')
            (3, 'tabela progressiva ganho capital'),
        ])

    cursor.execute("SELECT COUNT(*) FROM tipo_entrada")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO tipo_entrada (
                id_tipo, descricao_tipo, incide_ir, tipo_tabela_progressiva, tem_deducao_tabela_progressiva,
                imposto_alternativo, porcentagem_imposto_alternativo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            (1, 'Salário (CLT)', True, 1, True, None, None),
            (2, 'Aposentadoria', True, 2, True, None, None),
            (3, 'Aluguéis', True, 1, True, None, None),
            (4, 'Rendimentos não tributáveis', False, 1, True, None, None),
            (5, 'Venda de imóveis', False, None, False, 'ITBI', 3.2),
            (6, 'Venda de bens móveis', False, None, False, '', 5.0),
            (7, 'Recebimento de doação', False, None, False, 'Doação', 4.0),
            (8, 'Recebimento de herança', False, None, False, 'Herança', 0.0),
            (9, 'Ganho de capital em operações de compra e venda', True, 3, False, None, None),
            (10, 'Participação majoritária em Offshore', True, 1, False, None, None),
            (11, 'Rendimento no exterior', True, 1, False, None, None)
        ])
    cursor.execute("SELECT COUNT(*) FROM tabela_progressiva")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO tabela_progressiva (
                id_tabela_progressiva, valor_superior_faixa, aliquota, deducao
            )
            VALUES (?, ?, ?, ?)
        """, [
            # Tabela 1 – IRPF padrão
            (1, 2259.20,   0.0,     0.0),
            (1, 2826.65,   7.5,   169.44),
            (1, 3751.05,  15.0,   381.44),
            (1, 4664.68,  22.5,   662.77),
            (1, 999999999,  27.5,   896.00),

            # Tabela 2 – IRPF aposentados
            (2, 2259.20,   0.0,     0.0),
            (2, 2826.65,   7.5,   169.44),
            (2, 3751.05,  15.0,   381.44),
            (2, 4664.68,  22.5,   662.77),
            (2, 999999999,  27.5,   896.00),

            # Tabela 3 – Ganho de capital
            (3, 5000000.00,   15.0,       0.0),
            (3, 10000000.00,   17.5,    0.0),
            (3, 30000000.00,  20.0,    0.0),
            (3, 999000000.00,  22.5,    0.0)
        ])
        print("✅ Faixas da tabela progressiva inseridas com sucesso.")

    conn.commit()
    conn.close()
