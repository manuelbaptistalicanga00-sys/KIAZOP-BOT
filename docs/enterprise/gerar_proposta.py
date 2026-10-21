"""Gera o PDF comercial a partir da secção 10.3 do plano.
Dependência opcional: pip install reportlab (não é dependência do bot).
"""
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent
FONT = Path('/usr/share/fonts/truetype/dejavu')
if (FONT / 'DejaVuSans.ttf').exists():
    pdfmetrics.registerFont(TTFont('BOSans', str(FONT / 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('BOSans-Bold', str(FONT / 'DejaVuSans-Bold.ttf')))
    pdfmetrics.registerFontFamily('BOSans', normal='BOSans', bold='BOSans-Bold')
    family = 'BOSans'
else:
    family = 'Helvetica'

INK = colors.HexColor('#142b40')
MUTED = colors.HexColor('#526777')
BLUE = colors.HexColor('#2563eb')
styles = getSampleStyleSheet()
body = ParagraphStyle('BOBody', fontName=family, fontSize=9.2, leading=15,
                      textColor=INK, spaceAfter=9, alignment=TA_LEFT)
heading = ParagraphStyle('BOHeading', parent=body, fontName=family + '-Bold',
                         fontSize=13, leading=18, textColor=BLUE, spaceBefore=15,
                         spaceAfter=8, keepWithNext=True)
title = ParagraphStyle('BOTitle', parent=body, fontName=family + '-Bold',
                       fontSize=33, leading=41, spaceAfter=22)
small = ParagraphStyle('BOSmall', parent=body, fontSize=8, leading=13, textColor=MUTED)
eyebrow = ParagraphStyle('BOEyebrow', parent=body, fontName=family + '-Bold',
                         fontSize=9, leading=15, textColor=BLUE, spaceAfter=16)


def markup(text):
    text = html.escape(text)
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)


def para(text, style=body):
    return Paragraph(markup(text), style)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#e3e8ed'))
    canvas.line(22 * mm, 21 * mm, 188 * mm, 21 * mm)
    canvas.setFont(family, 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(22 * mm, 16 * mm, 'BOT OPTIMIZATION · Modelo sujeito a preenchimento e revisão jurídica')
    canvas.drawRightString(188 * mm, 16 * mm, str(doc.page))
    if doc.page > 1:
        canvas.setFont(family + '-Bold', 8)
        canvas.setFillColor(INK)
        canvas.drawString(22 * mm, 284 * mm, 'BOT OPTIMIZATION / PROPOSTA BO-001')
    canvas.restoreState()


story = [Spacer(1, 24 * mm), para('BOT OPTIMIZATION / SALES OPERATIONS', eyebrow),
         para('Cada oportunidade.<br/>Uma próxima acção.'.replace('<br/>', '\n'), title)]
# Usar Paragraph com quebra explícita no título, sem converter markup externo.
story[-1] = Paragraph('Cada oportunidade.<br/>Uma próxima acção.', title)
story += [para('Piloto de operação comercial por WhatsApp', heading),
          para('Implementação supervisionada de um processo de resposta, qualificação e acompanhamento. '
               'Conhecimento aprovado, responsável por oportunidade e critérios de avaliação acordados.'),
          Spacer(1, 12 * mm)]
cards = Table([
    [para('INVESTIMENTO', eyebrow), para('DURAÇÃO', eyebrow), para('ESCOPO', eyebrow)],
    [para('US$1.500', heading), para('14 dias', heading), para('1 processo', heading)],
    [para('Antes de impostos e terceiros', small), para('Após pré-requisitos', small), para('Até 1 número elegível', small)],
], colWidths=[55 * mm] * 3)
cards.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5fc')),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('LEFTPADDING', (0, 0), (-1, -1), 12), ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ('TOPPADDING', (0, 0), (-1, 0), 14), ('BOTTOMPADDING', (0, -1), (-1, -1), 14),
]))
story += [cards, Spacer(1, 15 * mm),
          para('Preparado para: [Entidade cliente]', heading),
          para('Fornecedor: [Entidade legal e NIF]\nData: [data] · Validade: 15 dias'),
          Spacer(1, 10 * mm),
          para('Sem garantia de vendas automáticas. A garantia cobre a entrega do fluxo técnico acordado. '
               'Este modelo não declara que integrações, SLA ou capacidades enterprise futuras já estejam disponíveis.', small),
          PageBreak()]
text = (ROOT / 'PLANO_PREMIUM.md').read_text(encoding='utf-8')
proposal = text.split('## 10.3 Proposta comercial completa', 1)[1].split('## 10.4', 1)[0].strip()
# Preservar uma única fonte textual para a proposta.
for block in proposal.split('\n\n'):
    block = block.strip()
    if not block:
        continue
    if block.startswith('### '):
        lines = block.splitlines()
        story.append(para(lines[0][4:], heading))
        if len(lines) > 1:
            story.append(Paragraph('<br/>'.join(markup(line) for line in lines[1:]), body))
    elif block.startswith('**Proposta BO-001'):
        story.append(para('Proposta BO-001 — Termos do piloto', heading))
    else:
        lines = block.splitlines()
        if len(lines) > 1:
            story.append(Paragraph('<br/>'.join(markup(line) for line in lines), body))
        else:
            story.append(para(block))
story += [Spacer(1, 12 * mm), KeepTogether([
    HRFlowable(width='100%', color=colors.HexColor('#ccd7df')),
    Spacer(1, 4 * mm), para('Checklist antes de assinar', heading),
    para('Preencher entidades/NIF e contactos; identificar o conector disponível e o número; '
         'confirmar datas e pré-requisitos; anexar DPA e fornecedores; acordar moeda/impostos; '
         'validar escopo e condições com assessoria jurídica.'),
])]
doc = SimpleDocTemplate(str(ROOT / 'PROPOSTA_COMERCIAL.pdf'), pagesize=(210 * mm, 297 * mm),
                        rightMargin=22 * mm, leftMargin=22 * mm,
                        topMargin=23 * mm, bottomMargin=28 * mm,
                        title='BOT OPTIMIZATION — Proposta comercial de piloto',
                        author='BOT OPTIMIZATION', subject='Modelo comercial B2B para personalização')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(ROOT / 'PROPOSTA_COMERCIAL.pdf')
