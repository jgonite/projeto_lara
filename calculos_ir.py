import sqlite3

VALOR_DEDUCAO_DEPENDENTE_ANUAL = 2275.08
LIMITE_SIMPLIFICADO = 564.80
ALIQUOTA_SIMPLIFICADA = 0.20

def calcular_dados_ir_por_tipo(conn, cpf):
    cursor = conn.cursor()

    cursor.execute("SELECT idade FROM usuario WHERE cpf = ?", (cpf,))
    idade = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dependente WHERE cpf_usuario = ?", (cpf,))
    qtd_dependentes = cursor.fetchone()[0]
    deducao_dependentes_total = qtd_dependentes * VALOR_DEDUCAO_DEPENDENTE_ANUAL
    deducao_dependentes_aplicada = False

    cursor.execute("""
        SELECT te.id_tipo, te.descricao_tipo, te.tipo_tabela_progressiva, te.tem_deducao_tabela_progressiva
        FROM tipo_entrada te
        JOIN entrada_mensal em ON em.id_tipo_entrada = te.id_tipo
        WHERE em.cpf_usuario = ? AND te.incide_ir = 1
        GROUP BY te.id_tipo
    """, (cpf,))
    tipos = cursor.fetchall()

    resultados = []

    for id_tipo, descricao_tipo, tipo_tabela_progressiva, tem_deducao in tipos:
        cursor.execute("""
            SELECT em.valor, em.valor_desconto, em.descricao_desconto
            FROM entrada_mensal em
            WHERE em.cpf_usuario = ? AND em.id_tipo_entrada = ?
        """, (cpf, id_tipo))
        linhas = cursor.fetchall()

        entradas_liquidas = []
        descontos_map = {}
        desconto_simplificado_total = 0
        contador_descontos = 1

        for valor, valor_desconto, descricao_desconto in linhas:
            desconto = valor_desconto or 0
            valor_real = valor - desconto
            entradas_liquidas.append(valor_real)

            if desconto > 0:
                descontos_map[contador_descontos] = {
                    "valor": desconto,
                    "descricao": descricao_desconto
                }
                contador_descontos += 1

        quantidade = len(entradas_liquidas)
        if quantidade == 0:
            continue

        # Aplicar dedução simplificada (20%, limitado a 564.80 por entrada)


        # Soma total das entradas já com descontos manuais
        total_entradas_liquidas = sum(entradas_liquidas)

        # Dedução por idade (aposentadoria)
        cursor.execute("""
            SELECT aliquota, deducao, idade_deducao_adicional, deducao_adicional
            FROM tabela_progressiva
            WHERE id_tabela_progressiva = ?
            ORDER BY valor_superior_faixa DESC
            LIMIT 1
        """, (tipo_tabela_progressiva,))
        _, _, idade_deducao_adicional, deducao_adicional_unitaria = cursor.fetchone()

        deducao_aposentadoria = deducao_adicional_unitaria * quantidade if idade > idade_deducao_adicional else 0

        # Dedução por dependentes (somente 1 vez)
        deducao_dependentes = 0
        if tem_deducao and not deducao_dependentes_aplicada and deducao_dependentes_total > 0:
            deducao_dependentes = deducao_dependentes_total
            deducao_dependentes_aplicada = True

        deducao_simplificada_total = 0
        if tipo_tabela_progressiva == 1 or tipo_tabela_progressiva == 2:
            descontos_simplificados = [
                min(valor * ALIQUOTA_SIMPLIFICADA, LIMITE_SIMPLIFICADO)
                for valor in entradas_liquidas
            ]
            deducao_simplificada_total = sum(descontos_simplificados)
            base_calculo = (
                    total_entradas_liquidas -
                    deducao_simplificada_total -
                    deducao_aposentadoria -
                    deducao_dependentes
            )
        else:
            base_calculo = total_entradas_liquidas

        # Buscar faixa progressiva baseada na base líquida
        cursor.execute("""
            SELECT aliquota, deducao
            FROM tabela_progressiva
            WHERE id_tabela_progressiva = ? AND valor_superior_faixa >= ?
            ORDER BY valor_superior_faixa ASC
            LIMIT 1
        """, (tipo_tabela_progressiva, base_calculo/quantidade))
        faixa = cursor.fetchone()

        if not faixa:
            # Se não encontrou, usa o teto
            cursor.execute("""
                SELECT aliquota, deducao
                FROM tabela_progressiva
                WHERE id_tabela_progressiva = ?
                ORDER BY valor_superior_faixa DESC
                LIMIT 1
            """, (tipo_tabela_progressiva,))
            faixa = cursor.fetchone()

        aliquota_pct, deducao_faixa = faixa
        aliquota = aliquota_pct / 100

        deducao_total_faixa = quantidade * deducao_faixa

        # Cálculo final do imposto
        valor_total_recolher = base_calculo * aliquota - (deducao_total_faixa if tem_deducao else 0)
        valor_total_recolher = max(0, valor_total_recolher)

        resultados.append({
            'descricao_tipo': descricao_tipo,
            'valor_total_declarado': total_entradas_liquidas,
            'deducao_simplificada_total': deducao_simplificada_total,
            'deducao_aposentadoria': deducao_aposentadoria,
            'deducao_dependentes': deducao_dependentes,
            'aliquota': aliquota_pct,
            'deducao_total': deducao_total_faixa if tem_deducao else 0,
            'valor_total_recolher': valor_total_recolher,
            'descontos': descontos_map
        })

    return resultados
