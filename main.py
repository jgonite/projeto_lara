from modelos import criar_tabelas
from seed import popular_tabelas_fixas
from db import get_connection


def inicializar_banco():
    criar_tabelas()
    popular_tabelas_fixas()


def exibir_menu_principal():
    print("\n🐊 Bem-vindo ao COCODRILO - seu declarador de imposto de renda anual!")
    print("Adicione usuários, seus dados de renda, e receba um extrato PDF com todas as informações")
    print("para te auxiliar na declaração, incluindo seu cálculo personalizado de IR.\n")

    while True:
        print("🔸 Menu Principal:")
        print("1 - Cadastrar/Alterar um usuário")
        print("2 - Alterar dados de renda de um usuário")
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
    conn.close()

    if user:
        print(f"\n🔍 Usuário selecionado: {user[0]}")
    else:
        print("❌ Usuário não encontrado.")

    input("\nPressione Enter para voltar ao menu principal...\n")



def submenu_pdf():
    print("\n📄 Submenu: Gerar PDF do Imposto de Renda")
    input("Pressione Enter para voltar ao menu principal...\n")


if __name__ == '__main__':
    inicializar_banco()
    exibir_menu_principal()
