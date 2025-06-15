
# Os métodos neste arquivo são responsáveis por toda a regra de negócio relacionada aos cálculos de Imposto de Renda
# para um determinado usuário cadastrado no sistema.
# O sistema permite o cadastro de diferentes tipos de renda (i.e. Salários, Aluguéis, Aposentadorias, venda de bens etc.)
# Cada uma destas rendas é tributada de maneira diferente, e o código desenvolvido aqui diferencia cada um destes cenários.

VALOR_DEDUCAO_DEPENDENTE_ANUAL = 2275.08
LIMITE_SIMPLIFICADO = 564.80
ALIQUOTA_SIMPLIFICADA = 0.20

def calcular_dados_ir_por_tipo(conn, cpf):
    cursor = conn.cursor()

    # Recupera a idade do usuário para verificar se ele possui a dedução adicional relacionada aos recebimentos de
    # aposentadoria para pessoas maiores de 65 anos.
    cursor.execute("SELECT idade FROM usuario WHERE cpf = ?", (cpf,))
    idade = cursor.fetchone()[0]

    # Verifica o número de dependentes do usuário, para aplicar a dedução adicional de 2275.08 por dependente
    cursor.execute("SELECT COUNT(*) FROM dependente WHERE cpf_usuario = ?", (cpf,))
    qtd_dependentes = cursor.fetchone()[0]
    deducao_dependentes_total = qtd_dependentes * VALOR_DEDUCAO_DEPENDENTE_ANUAL

    # Esta variável é importante pois a dedução por dependente é aplicada somente a um dos tipos renda do usuário.
    # Por exemplo, se o usuário recebe salário e aluguel, a dedução por dependentes será aplicada somente ao salário.
    deducao_dependentes_aplicada = False

    # Recupera os recebimentos (entradas) mensais do usuário, junto com seus diferentes 'tipos' (i.e. salário, alguel, venda etc.)
    cursor.execute("""
        SELECT te.id_tipo, te.descricao_tipo, te.tipo_tabela_progressiva, te.tem_deducao_tabela_progressiva
        FROM tipo_entrada te
        JOIN entrada_mensal em ON em.id_tipo_entrada = te.id_tipo
        WHERE em.cpf_usuario = ? AND te.incide_ir = 1
        GROUP BY te.id_tipo
    """, (cpf,))
    tipos = cursor.fetchall()

    # A variável resultados vai conter um dicionário para cada diferente tipo_entrada que o usuário tiver
    resultados = []

    # LOOP PRINCIPAL: para cada tipo de entrada que o usuário possuir
    for id_tipo, descricao_tipo, tipo_tabela_progressiva, tem_deducao in tipos:

        # Recupera agora apenas as entradas do usuário que são do tipo de entrada que estamos vendo nesta volta do loop
        cursor.execute("""
            SELECT em.valor, em.valor_desconto, em.descricao_desconto
            FROM entrada_mensal em
            WHERE em.cpf_usuario = ? AND em.id_tipo_entrada = ?
        """, (cpf, id_tipo))
        linhas = cursor.fetchall()

        # Algumas entradas possuem "desconto" no valor tributado. Especificamente, no caso de venda de imóveis, o usuário
        # precisa cadastrar por quanto vendeu este imóvel e por quanto comprou ele originalmente. O valor tributado é
        # a diferença (ganho de capital). No entanto, o sistema pergunta se o usuário comprou outro imóvel no período de
        # 6 meses desta venda pois, caso o tenha feito, esse valor de compra entrará como "desconto" no valor tributado.]
        # As entradas líquidas são os valores recebidos pelo usuário já descontado os valores de "desconto"
        entradas_liquidas = []

        # Geramos um dicionário de descontos pois queremos registrá-los para explicar isso no PDF
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

        # Soma total das entradas já com descontos
        total_entradas_liquidas = sum(entradas_liquidas)

        # Recuperamos agora da tabela progressiva qual é a alíquota, deducao e deducoes adicionais para o tipo de entrada
        # que estamos analisando nesta volta do loop
        cursor.execute("""
            SELECT aliquota, deducao, idade_deducao_adicional, deducao_adicional
            FROM tabela_progressiva
            WHERE id_tabela_progressiva = ?
            ORDER BY valor_superior_faixa DESC
            LIMIT 1
        """, (tipo_tabela_progressiva,))
        _, _, idade_deducao_adicional, deducao_adicional_unitaria = cursor.fetchone()

        # No caso de aposentadoria, existe uma deducao adicional que é aplicada apenas para os usuários acima de 65 anos
        # (o valor da dedução de idade estão cadastrados na tabela_progressiva)
        deducao_aposentadoria = deducao_adicional_unitaria * quantidade if idade > idade_deducao_adicional else 0

        # Dedução por dependentes (somente 1 vez)
        deducao_dependentes = 0
        if tem_deducao and not deducao_dependentes_aplicada and deducao_dependentes_total > 0:
            deducao_dependentes = deducao_dependentes_total
            deducao_dependentes_aplicada = True

        # Aqui geramos a base de cálculo para o somatório das entradas do tipo que estamos analisando nesta volta do loop.
        # No caso das tabelas progressivas 1 (salários, aluguéis) e 2 (aposentadoria), aplica-se a base de cálculo tanto
        # o desconto simplificado de 20% limitado a 564.80. Em contrapartida, para tabela progressiva 3 (ganho de capital)
        # a base de cálculo é simplesmente a soma das entradas líquidas
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

        # Agora com a base de cálculo de fato obtida, vamos procurar na tabela progressiva correta qual é a alíquota
        # a ser aplicada. A base de cálculo é dividida pela quantidade pois as tabelas progressivas estão cadastradas
        # com valores mensais.
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

        # Cálculo final do imposto: base de cálculo vezes alíquota menos a dedução específica da faixa)
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
