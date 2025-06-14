from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Table, TableStyle, PageBreak)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
import sqlite3
from datetime import datetime
from calculos_ir import calcular_dados_ir_por_tipo
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.platypus import Image, Spacer
from reportlab.lib.units import inch


def adicionar_grafico_pizza(story, resultados):
    labels = []
    valores = []

    for item in resultados:
        if item['valor_total_recolher'] > 0:
            labels.append(item['descricao_tipo'])
            valores.append(item['valor_total_recolher'])

    if not valores:
        return  # Não há dados para o gráfico

    total_recolher = sum(valores)

    def format_label(pct, allvals):
        valor_absoluto = pct / 100.0 * sum(allvals)
        return f"{pct:.1f}%\nR${valor_absoluto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    wedges, texts, autotexts = ax.pie(
        valores,
        labels=labels,
        autopct=lambda pct: format_label(pct, valores),
        startangle=140,
        textprops={'fontsize': 8}
    )

    ax.axis('equal')
    plt.title(
        'Distribuição do Imposto por Tipo de Rendimento',
        fontsize=14,
        pad=20  # aumenta o espaçamento vertical
    )

    # Salvar em buffer de memória
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)

    # Inserir no PDF
    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]
    story.append(Spacer(1, 20))
    story.append(Image(buf, width=5.5 * inch, height=3.5 * inch))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Total de Imposto a Recolher:</b> R$ {total_recolher:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), style_normal))


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

    # removi a consulta entradas, pois não vamos usar a tabela de rendimentos antiga aqui

    nome_arquivo = f"relatorio_rendimentos_{cpf}.pdf"
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="Label", fontSize=11, spaceAfter=6, leading=14))
    styles.add(
        ParagraphStyle(name="Subtitle", fontSize=12, spaceAfter=4, leading=14, leftIndent=0, fontName='Helvetica-Bold'))

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
    elementos.append(Paragraph("Este sistema foi construído para fins educativos e seus cálculos, embora reflitam parte das regras de declarações de Imposto de Renda reais, não devem ser usados como referência para declarações de Imposto de Renda.",
                               styles['Small']))
    elementos.append(PageBreak())

    # Nova página 2 - Cálculos Referentes ao IR
    elementos.append(Paragraph("Cálculos Referentes ao IR", styles['Title']))
    elementos.append(Spacer(1, 0.5 * cm))

    resultados = calcular_dados_ir_por_tipo(conn, cpf)

    for res in resultados:
        elementos.append(Paragraph(res['descricao_tipo'], styles['Subtitle']))
        elementos.append(Spacer(1, 0.2 * cm))
        dados_tabela = [
            ["Valor total declarado", f"R$ {res['valor_total_declarado']:.2f}"]
        ]

        if res['deducao_simplificada_total'] > 0:
            dados_tabela.append(["Desconto simplificado", f"R$ {res['deducao_simplificada_total']:.2f}"])

        if res['deducao_aposentadoria'] > 0:
            dados_tabela.append(["Dedução por aposentadoria", f"R$ {res['deducao_aposentadoria']:.2f}"])

        if res['deducao_dependentes'] > 0:
            dados_tabela.append(["Dedução por dependentes", f"R$ {res['deducao_dependentes']:.2f}"])

        dados_tabela.append(["Alíquota", f"{res['aliquota']:.2f}%"])

        if res['deducao_total'] > 0:
            dados_tabela.append(["Dedução Tabela Progressiva", f"R$ {res['deducao_total']:.2f}"])

        dados_tabela.append(["Valor total a recolher", f"R$ {res['valor_total_recolher']:.2f}"])

        tabela = Table(dados_tabela, colWidths=[9 * cm, 7 * cm], hAlign='LEFT')
        tabela.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
            ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))

        elementos.append(tabela)
        if res['descontos']:
            elementos.append(Spacer(1, 0.2 * cm))
            elementos.append(Paragraph("<b>Descontos aplicados:</b>", styles['Label']))
            for idx, dados in res['descontos'].items():
                val = f"R$ {dados['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                elementos.append(Paragraph(f"• {dados['descricao']}: {val}", styles['Small']))

        elementos.append(Spacer(1, 1 * cm))

    adicionar_grafico_pizza(elementos, resultados)

    conn.close()

    doc.build(elementos)
    print(f"✅ PDF salvo como {nome_arquivo}")