def mes_nome(mes_num):
    nomes = [
        "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
        "Jul", "Ago", "Set", "Out", "Nov", "Dez"
    ]
    return nomes[mes_num - 1] if 1 <= mes_num <= 12 else "Inválido"