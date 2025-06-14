import sqlite3

def calcular_outros_impostos(conn, cpf):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT te.id_tipo, te.descricao_tipo, te.imposto_alternativo, te.porcentagem_imposto_alternativo
        FROM tipo_entrada te
        JOIN entrada_mensal em ON em.id_tipo_entrada = te.id_tipo
        WHERE em.cpf_usuario = ? AND te.incide_ir = 0
        GROUP BY te.id_tipo
    """, (cpf,))

    tipos = cursor.fetchall()
    resultados = []

    for id_tipo, descricao_tipo, imposto_alternativo, porcentagem in tipos:
        cursor.execute("""
            SELECT valor, valor_desconto
            FROM entrada_mensal
            WHERE cpf_usuario = ? AND id_tipo_entrada = ?
        """, (cpf, id_tipo))

        linhas = cursor.fetchall()
        valores_liquidos = [(valor - (valor_desconto or 0)) for valor, valor_desconto in linhas]
        valor_total_declarado = sum(valores_liquidos)

        if imposto_alternativo is None:
            resultado = {
                'descricao_tipo': descricao_tipo,
                'valor_total_declarado': valor_total_declarado,
                'imposto_a_recolher': "Nenhum. Rendimento isento de impostos.",
                'aliquota': None,
                'valor_a_recolher': 0
            }
        else:
            aliquota = porcentagem / 100
            valor_a_recolher = valor_total_declarado * aliquota
            resultado = {
                'descricao_tipo': descricao_tipo,
                'valor_total_declarado': valor_total_declarado,
                'imposto_a_recolher': imposto_alternativo,
                'aliquota': porcentagem,
                'valor_a_recolher': valor_a_recolher
            }

        resultados.append(resultado)

    return resultados
