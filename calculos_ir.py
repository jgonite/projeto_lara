import sqlite3

def obter_faixa_tabela_progressiva(conn, tipo_tabela_progressiva, valor_total):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT valor_superior_faixa, aliquota, deducao
        FROM tabela_progressiva
        WHERE id_tabela_progressiva = ?
          AND valor_superior_faixa >= ?
        ORDER BY valor_superior_faixa ASC
        LIMIT 1
    """, (tipo_tabela_progressiva, valor_total))
    faixa = cursor.fetchone()
    if faixa:
        valor_superior, aliquota, deducao = faixa
        return aliquota, deducao
    else:
        # Se não encontrou faixa, busca a maior faixa (teto)
        cursor.execute("""
            SELECT aliquota, deducao
            FROM tabela_progressiva
            WHERE id_tabela_progressiva = ?
            ORDER BY valor_superior_faixa DESC
            LIMIT 1
        """, (tipo_tabela_progressiva,))
        faixa = cursor.fetchone()
        if faixa:
            aliquota, deducao = faixa
            return aliquota, deducao
        else:
            return 0, 0


def calcular_dados_ir_por_tipo(conn, cpf_usuario):
    cursor = conn.cursor()

    # Seleciona todos os tipos de entrada com incide_ir=True para esse usuário
    cursor.execute("""
        SELECT te.id_tipo, te.descricao_tipo, te.tipo_tabela_progressiva
        FROM tipo_entrada te
        WHERE te.incide_ir = 1
        AND EXISTS (
            SELECT 1 FROM entrada_mensal em
            WHERE em.cpf_usuario = ?
              AND em.id_tipo_entrada = te.id_tipo
        )
    """, (cpf_usuario,))
    tipos_entrada = cursor.fetchall()

    resultados = []
    for id_tipo, descricao_tipo, tipo_tabela_progressiva in tipos_entrada:
        # Soma das entradas mensais para o tipo de entrada
        cursor.execute("""
            SELECT SUM(valor)
            FROM entrada_mensal
            WHERE cpf_usuario = ?
              AND id_tipo_entrada = ?
        """, (cpf_usuario, id_tipo))
        soma_valor = cursor.fetchone()[0] or 0

        if soma_valor == 0:
            continue

        # Busca aliquota e deducao pela tabela progressiva correta
        aliquota, deducao = obter_faixa_tabela_progressiva(conn, tipo_tabela_progressiva, soma_valor)

        valor_a_recolher = soma_valor * aliquota - deducao

        # Não permitir valor negativo a recolher
        if valor_a_recolher < 0:
            valor_a_recolher = 0

        resultados.append({
            "descricao_tipo": descricao_tipo,
            "valor_total_declarado": soma_valor,
            "aliquota": aliquota,
            "deducao": deducao,
            "valor_total_a_recolher": valor_a_recolher
        })

    return resultados