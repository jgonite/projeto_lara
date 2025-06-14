from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Table, TableStyle, PageBreak)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
import sqlite3
from datetime import datetime


def gerar_pdf_rendimentos(cpf):
    conn = sqlite3.connect("imposto_renda.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nome_completo, idade, profissao
        FROM usuario
        WHERE cpf = ?
    """, (cpf,))
    usuario = cursor.fetchone()
    if not usuario:
        print("❌ Usuário não encontrado.")
        return

    nome, idade, profissao = usuario

    cursor.execute("""
                   SELECT nome_completo
                   FROM dependente
                   WHERE cpf_usuario = ?
                   """, (cpf,))
    dependentes = [row[0] for row in cursor.fetchall()]

    cursor.execute("""
        SELECT em.data_entrada, te.descricao_tipo, em.valor
        FROM entrada_mensal em
        JOIN tipo_entrada te ON em.id_tipo_entrada = te.id_tipo
        WHERE em.cpf_usuario = ?
    """, (cpf,))
    entradas = cursor.fetchall()
    conn.close()

    rendimentos_por_mes = {i: [] for i in range(1, 13)}
    for data, tipo, valor in entradas:
        try:
            mes = int(data.split("/")[0])
            rendimentos_por_mes[mes].append((tipo, valor))
        except:
            continue

    nome_arquivo = f"relatorio_rendimentos_{cpf}.pdf"
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="Label", fontSize=11, spaceAfter=6, leading=14))

    def header_footer(canvas_obj, doc):
        canvas_obj.saveState()
        width, height = A4
        now = datetime.now().strftime('%d/%m/%Y')
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawString(2 * cm, height - 1.5 * cm, f"Relatório IRPF - {nome}")
        canvas_obj.drawRightString(width - 2 * cm, height - 1.5 * cm, f"Data: {now}")
        canvas_obj.drawRightString(width - 2 * cm, 1.5 * cm, f"Página {doc.page}")
        canvas_obj.restoreState()

    doc = BaseDocTemplate(nome_arquivo, pagesize=A4,
                          leftMargin=2.5 * cm, rightMargin=2.5 * cm,
                          topMargin=3 * cm, bottomMargin=2.5 * cm)

    frame = Frame(doc.leftMargin, doc.bottomMargin,
                  doc.width, doc.height, id='normal')

    doc.addPageTemplates([PageTemplate(id='Report', frames=frame, onPage=header_footer)])

    elementos = []

    # Capa
    elementos.append(Paragraph("Informações Referentes ao <br/><b>IRPF 2025</b>", styles['Title']))
    elementos.append(Spacer(1, 1 * cm))
    elementos.append(Paragraph(f"<b>Nome:</b> {nome}", styles['Label']))
    elementos.append(Paragraph(f"<b>CPF:</b> {cpf}", styles['Label']))
    elementos.append(Paragraph(f"<b>Idade:</b> {idade}", styles['Label']))
    elementos.append(Paragraph(f"<b>Profissão:</b> {profissao}", styles['Label']))
    if dependentes:
        elementos.append(Paragraph(f"<b>Dependentes:</b>", styles['Label']))
        lista_dependentes = "<br/>".join([f"• {nome}" for nome in dependentes])
        elementos.append(Paragraph(lista_dependentes, styles['Small']))
    else:
        elementos.append(Paragraph(f"<b>Dependentes:</b> Nenhum", styles['Label']))
    elementos.append(Spacer(1, 2 * cm))
    elementos.append(Paragraph("Documento gerado automaticamente pelo sistema COCODRILO 2025.",
                                styles['Small']))
    elementos.append(PageBreak())

    # Tabela de rendimentos
    elementos.append(Paragraph("Demonstrativo Mensal de Rendimentos", styles['Heading2']))
    elementos.append(Spacer(1, 0.5 * cm))

    dados_tabela = [["Mês", "Rendimentos"]]
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
             "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

    for i in range(1, 13):
        rendimentos = rendimentos_por_mes[i]
        if not rendimentos:
            texto = "-"
        else:
            texto = ", ".join([f"{tipo}: R${valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                               for tipo, valor in rendimentos])
        dados_tabela.append([meses[i - 1], texto])

    tabela = Table(dados_tabela, colWidths=[4 * cm, 12 * cm])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
    ]))
    elementos.append(tabela)

    doc.build(elementos)
    print(f"✅ PDF salvo como {nome_arquivo}")
