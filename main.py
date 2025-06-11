
from modelos import criar_tabelas
from seed import popular_tabelas_fixas
from db import get_connection
from utils import mes_nome
from datetime import datetime
import sqlite3
from gerar_pdf import gerar_pdf_rendimentos


def inicializar_banco():
    criar_tabelas()
    popular_tabelas_fixas()


def exibir_menu_principal():
    print("\n🐊 Bem-vindo ao COCODRILO 2025 - seu declarador de imposto de renda para 2025!")
    print("Adicione usuários, seus dados de renda, e receba um extrato PDF com todas as informações")
    print("para te auxiliar na declaração, incluindo seu cálculo personalizado de IR de 2025.\n")

    while True:
        print("🔸 Menu Principal:")
        print("1 - Cadastrar/Editar um usuário")
        print("2 - Cadastrar/Editar dados de renda de um usuário")
        print("3 - Gerar PDF do imposto de renda para um usuário")
        print("0 - Sair")

        escolha = input("Escolha uma opção: ").strip()

        if escolha == '1':
            submenu_usuario()
        elif escolha == '2':
            submenu_renda()
        elif escolha == '3':
            submenu_pdf()
        elif escolha == '0':
            print("Encerrando o programa. Até logo! 👋")
            break
        else:
            print("Opção inválida. Tente novamente.")


def submenu_usuario():
    while True:
        print("\n🧑 Submenu: Cadastrar/Alterar Usuário")
        print("1 - Adicionar novo usuário")
        print("2 - Alterar idade ou profissão de um usuário")
        print("3 - Remover um usuário")
        print("0 - Voltar ao menu principal")

        escolha = input("Escolha uma opção: ").strip()

        if escolha == '1':
            adicionar_usuario()
        elif escolha == '2':
            alterar_usuario()
        elif escolha == '3':
            remover_usuario()
        elif escolha == '0':
            break
        else:
            print("Opção inválida. Tente novamente.")


def adicionar_usuario():
    conn = get_connection()
    cursor = conn.cursor()

    print("\n📋 Adicionar novo usuário:")
    cpf = input("CPF: ").strip()
    nome = input("Nome completo: ").strip()
    idade = input("Idade: ").strip()
    profissao = input("Profissão: ").strip()

    try:
        cursor.execute("""
                       INSERT INTO usuario (cpf, nome_completo, idade, profissao)
                       VALUES (?, ?, ?, ?)
                       """, (cpf, nome, int(idade), profissao))
        conn.commit()
        print("\n✅ Usuário cadastrado com sucesso!\n")
    except Exception as e:
        print(f"❌ Erro ao cadastrar usuário: {e}")
    finally:
        conn.close()

    listar_usuarios()
    input("\nPressione Enter para voltar ao menu...")


def listar_usuarios(retornar_lista=False):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT cpf, nome_completo FROM usuario")
    usuarios = cursor.fetchall()
    conn.close()

    if not usuarios:
        print("\nℹ️ Nenhum usuário cadastrado.")
        return [] if retornar_lista else None

    print("\n👥 Lista de usuários:")
    for cpf, nome in usuarios:
        print(f"{cpf} - {nome}")

    return usuarios if retornar_lista else None


def alterar_usuario():
    usuarios = listar_usuarios(retornar_lista=True)
    if not usuarios:
        input("\nPressione Enter para voltar ao menu...")
        return

    cpf = input("\nDigite o CPF do usuário que deseja alterar: ").strip()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nome_completo, idade, profissao FROM usuario WHERE cpf = ?", (cpf,))
    user = cursor.fetchone()

    if not user:
        print("❌ Usuário não encontrado.")
    else:
        print(f"\nAlterando dados de {user[0]}:")
        nova_idade = input(f"Nova idade (atual: {user[1]}): ").strip()
        nova_profissao = input(f"Nova profissão (atual: {user[2]}): ").strip()

        cursor.execute("""
                       UPDATE usuario
                       SET idade     = ?,
                           profissao = ?
                       WHERE cpf = ?
                       """, (int(nova_idade), nova_profissao, cpf))
        conn.commit()
        print("✅ Dados atualizados com sucesso.")

    conn.close()
    input("\nPressione Enter para voltar ao menu...")


def remover_usuario():
    usuarios = listar_usuarios(retornar_lista=True)
    if not usuarios:
        input("\nPressione Enter para voltar ao menu...")
        return

    cpf = input("\nDigite o CPF do usuário que deseja remover: ").strip()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nome_completo FROM usuario WHERE cpf = ?", (cpf,))
    user = cursor.fetchone()

    if not user:
        print("❌ Usuário não encontrado.")
    else:
        confirmacao = input(f"Tem certeza que deseja remover {user[0]}? (s/n): ").strip().lower()
        if confirmacao == 's':
            cursor.execute("DELETE FROM usuario WHERE cpf = ?", (cpf,))
            conn.commit()
            print("🗑️ Usuário removido com sucesso.")
        else:
            print("❎ Remoção cancelada.")

    conn.close()
    input("\nPressione Enter para voltar ao menu...")


def submenu_renda():
    print("\n💰 Submenu: Alterar Dados de Renda")

    usuarios = listar_usuarios(retornar_lista=True)
    if not usuarios:
        input("\nPressione Enter para voltar ao menu...")
        return

    cpf = input("\nDigite o CPF do usuário que deseja alterar os dados de renda: ").strip()

    # Verifica se o CPF existe
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nome_completo FROM usuario WHERE cpf = ?", (cpf,))
    user = cursor.fetchone()

    if not user:
        print("❌ Usuário não encontrado.")
        conn.close()
        input("\nPressione Enter para voltar ao menu principal...\n")
        return

    print(f"\n🔍 Usuário selecionado: {user[0]}")
    conn.close()

    while True:
        print("\n📊 Opções de Renda:")
        print("1 - Mostrar tabela de rendimentos cadastrados")
        print("2 - Cadastrar receita mensal recorrente")
        print("3 - Cadastrar receitas eventuais no ano")
        print("0 - Voltar ao menu principal")

        escolha = input("Escolha uma opção: ").strip()

        if escolha == '1':
            mostrar_rendimentos(cpf)
        elif escolha == '2':
            cadastrar_receita_recorrente(cpf)
        elif escolha == '3':
            cadastrar_receita_eventual(cpf)
        elif escolha == '0':
            break
        else:
            print("Opção inválida. Tente novamente.")

def mostrar_rendimentos(cpf):
    print(f"\n📊 Rendimentos cadastrados para CPF {cpf}")

    conn = get_connection()
    cursor = conn.cursor()

    ano_atual = datetime.now().year
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
             "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

    print("\nMês  | Rendimentos")
    print("-" * 40)

    for i, nome_mes in enumerate(meses, start=1):
        mes_formatado = f"{i:02d}/{ano_atual}"

        cursor.execute("""
            SELECT te.descricao_tipo, em.valor
            FROM entrada_mensal em
            JOIN tipo_entrada te ON em.id_tipo_entrada = te.id_tipo
            WHERE em.cpf_usuario = ? AND em.data_entrada = ?
        """, (cpf, mes_formatado))

        rendimentos = cursor.fetchall()

        if rendimentos:
            descricoes = [f"{desc}: {valor:.2f}" for desc, valor in rendimentos]
            linha = ', '.join(descricoes)
        else:
            linha = "-"

        print(f"{nome_mes:<4} | {linha}")

    conn.close()
    input("\nPressione Enter para voltar ao menu anterior...")

def cadastrar_receita_recorrente(cpf):
    print(f"\n➕ Cadastro de receita mensal recorrente para CPF {cpf}:")

    opcoes = {
        '1': ('Salário CLT', 1),
        '2': ('Aposentadoria', 2),
        '3': ('Aluguel', 3),
        '4': ('Bolsa de estudos', 4),
        '0': ('Voltar', None)
    }

    for chave, (desc, _) in opcoes.items():
        print(f"{chave}) {desc}")

    tipo = input("Escolha o tipo de receita: ").strip()
    if tipo not in opcoes or tipo == '0':
        print("Operação cancelada.")
        input("\nPressione Enter para voltar ao menu anterior...")
        return

    descricao_tipo, id_tipo = opcoes[tipo]

    try:
        primeiro_mes = int(input("\nDigite o número do primeiro mês de recebimento (1 - Jan, ..., 12 - Dez): ").strip())
        if primeiro_mes < 1 or primeiro_mes > 12:
            raise ValueError("Mês fora do intervalo")

        meses_validos = list(range(primeiro_mes, 13))
        gabarito = ", ".join([f"{m} - {mes_nome(m)}" for m in meses_validos])
        print(f"\nEscolha o último mês de recebimento entre: {gabarito}")
        ultimo_mes = int(input("Digite o número do último mês de recebimento: ").strip())
        if ultimo_mes not in meses_validos:
            raise ValueError("Último mês inválido")

        valor = float(input("\nDigite o valor bruto recebido: ").replace(',', '.'))
        if valor <= 0:
            raise ValueError("Valor inválido")

    except ValueError as ve:
        print(f"❌ Erro: {ve}")
        input("\nPressione Enter para voltar ao menu anterior...")
        return

    ano_atual = datetime.now().year
    registros_inseridos = 0

    conn = get_connection()
    cursor = conn.cursor()

    for mes in range(primeiro_mes, ultimo_mes + 1):
        data_entrada = f"{mes:02d}/{ano_atual}"
        cursor.execute("""
            INSERT INTO entrada_mensal (cpf_usuario, data_entrada, id_tipo_entrada, valor)
            VALUES (?, ?, ?, ?)
        """, (cpf, data_entrada, id_tipo, valor))
        registros_inseridos += 1

    conn.commit()
    conn.close()

    print(f"\n✅ {registros_inseridos} registros de '{descricao_tipo}' inseridos com sucesso para CPF {cpf}.")
    input("\nPressione Enter para voltar ao menu anterior...")


def cadastrar_receita_eventual(cpf):
    print(f"\n➕ Cadastro de receita eventual para CPF {cpf}:")

    opcoes = {
        '1': ('Salário CLT', 1),
        '2': ('Aposentadoria', 2),
        '3': ('Aluguel', 3),
        '4': ('Bolsa de estudos', 4),
        '5': ('Venda de imóvel', 5),
        '6': ('Venda de bens móveis', 6),
        '7': ('Recebimento de doação', 7),
        '8': ('Recebimento de herança', 8),
        '9': ('Participação majoritária em offshore', 10),
        '0': ('Voltar', None)
    }

    for chave, (desc, _) in opcoes.items():
        print(f"{chave}) {desc}")

    tipo = input("Escolha o tipo de receita: ").strip()
    if tipo not in opcoes or tipo == '0':
        print("Operação cancelada.")
        input("\nPressione Enter para voltar ao menu anterior...")
        return

    descricao_tipo, id_tipo = opcoes[tipo]

    try:
        if tipo == '9':
            valor = float(input("\nDigite o valor da receita **anual** derivada da participação em offshore: ").replace(',', '.'))
            if valor <= 0:
                raise ValueError("Valor inválido")
            mes = 12  # Arbitrário: usar Dezembro como referência da receita anual
        else:
            mes = int(input("\nDigite o mês de recebimento (1 - Jan, ..., 12 - Dez): ").strip())
            if mes < 1 or mes > 12:
                raise ValueError("Mês fora do intervalo")
            valor = float(input("\nDigite o valor da receita eventual: ").replace(',', '.'))
            if valor <= 0:
                raise ValueError("Valor inválido")
    except ValueError as ve:
        print(f"❌ Erro: {ve}")
        input("\nPressione Enter para voltar ao menu anterior...")
        return

    ano_atual = datetime.now().year
    data_entrada = f"{mes:02d}/{ano_atual}"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO entrada_mensal (cpf_usuario, data_entrada, id_tipo_entrada, valor)
        VALUES (?, ?, ?, ?)
    """, (cpf, data_entrada, id_tipo, valor))

    conn.commit()
    conn.close()

    print(f"\n✅ Receita eventual de '{descricao_tipo}' registrada com sucesso para CPF {cpf}.")
    input("\nPressione Enter para voltar ao menu anterior...")


def submenu_pdf():
    usuarios = listar_usuarios(retornar_lista=True)
    if not usuarios:
        input("\nPressione Enter para voltar ao menu...")
        return

    cpf = input("\nDigite o CPF do usuário para gerar o PDF: ").strip()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nome_completo FROM usuario WHERE cpf = ?", (cpf,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        print("❌ Usuário não encontrado.")
    else:
        gerar_pdf_rendimentos(cpf)
        print(f"\n✅ PDF gerado com sucesso: relatorio_rendimentos_{cpf}.pdf")

    input("\nPressione Enter para voltar ao menu...")



if __name__ == '__main__':
    inicializar_banco()
    exibir_menu_principal()
