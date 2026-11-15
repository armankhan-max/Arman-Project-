"""Builds the Over-60 Fit and Style Guide PDF from content/*.txt (light markup)."""
import glob, re, os
from reportlab.lib.pagesizes import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak,
                                Table, TableStyle, KeepTogether, NextPageTemplate, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FD = '/usr/share/fonts/truetype/dejavu/'
for n, f in [('Serif', 'DejaVuSerif.ttf'), ('Serif-B', 'DejaVuSerif-Bold.ttf'), ('Serif-I', 'DejaVuSerif-Italic.ttf'),
             ('Serif-BI', 'DejaVuSerif-BoldItalic.ttf'), ('Sans', 'DejaVuSans.ttf'), ('Sans-B', 'DejaVuSans-Bold.ttf'),
             ('SansC', 'DejaVuSansCondensed.ttf'), ('SansC-B', 'DejaVuSansCondensed-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(n, FD + f))
pdfmetrics.registerFontFamily('Serif', normal='Serif', bold='Serif-B', italic='Serif-I', boldItalic='Serif-BI')
pdfmetrics.registerFontFamily('Sans', normal='Sans', bold='Sans-B', italic='Sans', boldItalic='Sans-B')

NAVY = colors.HexColor('#1F2A44'); GOLD = colors.HexColor('#B8893B'); CREAM = colors.HexColor('#F6F1E7')
RED = colors.HexColor('#A23B2A'); GREEN = colors.HexColor('#2F6B45'); GREY = colors.HexColor('#5B5B5B')
LRED = colors.HexColor('#F7E6E2'); LGREEN = colors.HexColor('#E3F0E6'); LBLUE = colors.HexColor('#E6EBF4')

W, H = 6 * inch, 9 * inch
M = 0.62 * inch
TITLE = 'The Over-60 Fit and Style Guide'

S = {}
S['body'] = ParagraphStyle('body', fontName='Serif', fontSize=11.2, leading=16, spaceAfter=7, textColor=colors.HexColor('#1d1d1d'))
S['h1'] = ParagraphStyle('h1', fontName='Sans-B', fontSize=23, leading=28, textColor=NAVY, spaceAfter=6)
S['h2'] = ParagraphStyle('h2', fontName='Sans-B', fontSize=14.5, leading=18, textColor=NAVY, spaceBefore=10, spaceAfter=5)
S['h3'] = ParagraphStyle('h3', fontName='Sans-B', fontSize=11.8, leading=15, textColor=GOLD, spaceBefore=6, spaceAfter=3)
S['bul'] = ParagraphStyle('bul', parent=S['body'], leftIndent=14, bulletIndent=2, spaceAfter=3.5)
S['chk'] = ParagraphStyle('chk', parent=S['body'], leftIndent=18, bulletIndent=0, spaceAfter=4, bulletFontName='Sans', bulletFontSize=13)
S['num'] = ParagraphStyle('num', parent=S['body'], leftIndent=18, bulletIndent=0, spaceAfter=4, bulletFontName='Sans-B')
S['cell'] = ParagraphStyle('cell', fontName='Serif', fontSize=9.6, leading=12.4)
S['cellh'] = ParagraphStyle('cellh', fontName='Sans-B', fontSize=9.4, leading=12, textColor=colors.white)
S['box'] = ParagraphStyle('box', fontName='Serif', fontSize=10.6, leading=14.6)
S['boxh'] = ParagraphStyle('boxh', fontName='Sans-B', fontSize=9.5, leading=12, textColor=NAVY)
S['say'] = ParagraphStyle('say', fontName='Serif-I', fontSize=11, leading=15.5)
S['chapno'] = ParagraphStyle('chapno', fontName='Sans-B', fontSize=10, leading=13, textColor=GOLD)
S['lead'] = ParagraphStyle('lead', fontName='Serif-I', fontSize=11.8, leading=17, textColor=GREY, spaceAfter=10)

CW = W - 2 * M


def inline(t):
    t = t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = t.replace('\u2610', '<font name="Sans">\u2610</font>').replace('\u2713', '<font name="Sans">\u2713</font>').replace('\u2717', '<font name="Sans">\u2717</font>')
    t = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)', r'<i>\1</i>', t)
    return t


def callout(kind, text):
    cfg = {'TIP': ('TAILOR’S TIP', LBLUE, NAVY), 'WARN': ('WARNING', LRED, RED), 'NOTE': ('GOOD TO KNOW', CREAM, GOLD),
           'WHY': ('WHY THIS MATTERS', CREAM, GOLD), 'TRY': ('DO THIS TODAY', LGREEN, GREEN)}[kind]
    hs = ParagraphStyle('x', parent=S['boxh'], textColor=cfg[2])
    t = Table([[Paragraph(cfg[0], hs)], [Paragraph(inline(text), S['box'])]], colWidths=[CW])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), cfg[1]), ('LINEBEFORE', (0, 0), (0, -1), 3.5, cfg[2]),
                           ('LEFTPADDING', (0, 0), (-1, -1), 11), ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                           ('TOPPADDING', (0, 0), (-1, 0), 8), ('BOTTOMPADDING', (0, -1), (-1, -1), 9),
                           ('TOPPADDING', (0, 1), (-1, -1), 2)]))
    return [Spacer(1, 4), KeepTogether(t), Spacer(1, 8)]


def say_box(text):
    t = Table([[Paragraph('SAY THIS', ParagraphStyle('s', parent=S['boxh'], textColor=GOLD))],
               [Paragraph('“' + inline(text) + '”', S['say'])]], colWidths=[CW - 20])
    t.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, GOLD), ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                           ('LEFTPADDING', (0, 0), (-1, -1), 12), ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                           ('TOPPADDING', (0, 0), (-1, 0), 8), ('BOTTOMPADDING', (0, -1), (-1, -1), 10)]))
    o = Table([[t]], colWidths=[CW]); o.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 10)]))
    return [Spacer(1, 3), KeepTogether(o), Spacer(1, 7)]


def wr_box(title, wrong, right):
    hw = ParagraphStyle('hw', parent=S['cellh']);
    rows = [[Paragraph('✗  WRONG', hw), Paragraph('✓  RIGHT', hw)],
            [Paragraph(inline(wrong), S['cell']), Paragraph(inline(right), S['cell'])]]
    data = []
    if title:
        data.append([Paragraph(inline(title), ParagraphStyle('wt', parent=S['boxh'], fontSize=10.5)), ''])
    data += rows
    t = Table(data, colWidths=[CW / 2, CW / 2])
    o = 1 if title else 0
    st = [('BACKGROUND', (0, o), (0, o), RED), ('BACKGROUND', (1, o), (1, o), GREEN),
          ('BACKGROUND', (0, o + 1), (0, o + 1), LRED), ('BACKGROUND', (1, o + 1), (1, o + 1), LGREEN),
          ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
          ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 7)]
    if title:
        st += [('SPAN', (0, 0), (1, 0)), ('BACKGROUND', (0, 0), (1, 0), CREAM)]
    t.setStyle(TableStyle(st))
    return [Spacer(1, 3), KeepTogether(t), Spacer(1, 8)]


def table(rows, widths=None):
    n = len(rows[0])
    if widths is None:
        lens = [max(len(r[i]) if i < len(r) else 0 for r in rows) for i in range(n)]
        lens = [max(6, min(l, 60)) for l in lens]
        tot = sum(lens); widths = [CW * l / tot for l in lens]
    data = []
    for k, r in enumerate(rows):
        r = r + [''] * (n - len(r))
        data.append([Paragraph(inline(c), S['cellh'] if k == 0 else S['cell']) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [('BACKGROUND', (0, 0), (-1, 0), NAVY), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
          ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#C9C2B4')),
          ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
          ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]
    for k in range(1, len(data)):
        if k % 2 == 0:
            st.append(('BACKGROUND', (0, k), (-1, k), CREAM))
    t.setStyle(TableStyle(st))
    return [Spacer(1, 3), t, Spacer(1, 9)]


class Doc(BaseDocTemplate):
    def __init__(self, fn):
        super().__init__(fn, pagesize=(W, H), leftMargin=M, rightMargin=M, topMargin=0.7 * inch, bottomMargin=0.75 * inch,
                         title=TITLE, author='The Over-60 Fit and Style Guide',
                         subject='Fit, alterations and wardrobe guide for men over 60')
        fr = Frame(M, 0.75 * inch, CW, H - 1.45 * inch, id='f', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate('cover', [fr], onPage=cover_page),
                               PageTemplate('plain', [fr], onPage=plain_page),
                               PageTemplate('main', [fr], onPage=main_page),
                               PageTemplate('chap', [fr], onPage=chap_page)])
        self.chap = ''

    def afterFlowable(self, f):
        if hasattr(f, 'toc'):
            lvl, txt = f.toc
            self.notify('TOCEntry', (lvl, txt, self.page))
            if lvl == 0:
                self.chap = txt


def cover_page(c, d):
    c.saveState()
    c.setFillColor(NAVY); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setStrokeColor(GOLD); c.setLineWidth(1.2); c.rect(0.32 * inch, 0.32 * inch, W - 0.64 * inch, H - 0.64 * inch)
    c.setLineWidth(0.5); c.rect(0.4 * inch, 0.4 * inch, W - 0.8 * inch, H - 0.8 * inch)
    # tape measure motif
    y = 5.55 * inch; c.setFillColor(GOLD); c.rect(0.4 * inch, y, W - 0.8 * inch, 0.32 * inch, fill=1, stroke=0)
    c.setStrokeColor(NAVY); c.setFillColor(NAVY); c.setFont('SansC-B', 6.5)
    x0 = 0.4 * inch; k = 0
    while x0 + k * 0.125 * inch < W - 0.4 * inch:
        x = x0 + k * 0.125 * inch; ln = 0.16 if k % 8 == 0 else (0.11 if k % 4 == 0 else 0.06)
        c.setLineWidth(0.6); c.line(x, y + 0.32 * inch, x, y + (0.32 - ln) * inch)
        if k % 8 == 0 and k: c.drawCentredString(x, y + 0.05 * inch, str(k // 8 + 59))
        k += 1
    c.setFillColor(GOLD); c.setFont('Sans-B', 9.5)
    c.drawCentredString(W / 2, 7.75 * inch, 'A  PRACTICAL  FITTING-ROOM  GUIDE')
    c.setFillColor(colors.white); c.setFont('Serif-B', 30)
    for i, l in enumerate(['The Over-60', 'Fit and Style', 'Guide']):
        c.drawCentredString(W / 2, (7.05 - i * 0.48) * inch, l)
    c.setFont('Serif-I', 13); c.setFillColor(colors.HexColor('#E9DFC8'))
    for i, l in enumerate(['Know What Fits, What to Alter', 'and What to Buy']):
        c.drawCentredString(W / 2, (4.95 - i * 0.26) * inch, l)
    c.setStrokeColor(GOLD); c.setLineWidth(0.8); c.line(W / 2 - 0.6 * inch, 4.3 * inch, W / 2 + 0.6 * inch, 4.3 * inch)
    c.setFont('Serif', 11); c.setFillColor(colors.white)
    for i, l in enumerate(['The complete system for men over 60', 'to look sharp without wasting money']):
        c.drawCentredString(W / 2, (3.85 - i * 0.24) * inch, l)
    c.setFont('Sans', 8.5); c.setFillColor(GOLD)
    c.drawCentredString(W / 2, 1.05 * inch, 'FIT  •  ALTERATIONS  •  COLOUR  •  WARDROBE  •  SHOPPING  •  CARE')
    c.restoreState()


def footer(c, d):
    c.setFont('Sans', 8); c.setFillColor(GREY)
    c.drawCentredString(W / 2, 0.42 * inch, str(d.page))
    c.setStrokeColor(GOLD); c.setLineWidth(0.5); c.line(M, 0.58 * inch, W - M, 0.58 * inch)


def plain_page(c, d):
    c.saveState(); footer(c, d); c.restoreState()


def main_page(c, d):
    c.saveState(); footer(c, d)
    c.setFont('Sans', 7.5); c.setFillColor(GREY)
    c.drawString(M, H - 0.45 * inch, TITLE.upper())
    c.drawRightString(W - M, H - 0.45 * inch, (d.chap or '')[:48].upper())
    c.setStrokeColor(colors.HexColor('#D8D0C0')); c.setLineWidth(0.4); c.line(M, H - 0.52 * inch, W - M, H - 0.52 * inch)
    c.restoreState()


def chap_page(c, d):
    c.saveState(); footer(c, d)
    c.setFillColor(NAVY); c.rect(0, H - 0.22 * inch, W, 0.22 * inch, fill=1, stroke=0)
    c.setFillColor(GOLD); c.rect(0, H - 0.27 * inch, W, 0.05 * inch, fill=1, stroke=0)
    c.restoreState()


class HP(Paragraph):
    pass


def heading(text, style, lvl):
    p = HP(inline(text), style); p.toc = (lvl, text); return p


def parse(path, story):
    lines = open(path, encoding='utf-8').read().split('\n')
    i = 0; para = []

    def flush():
        if para:
            story.append(Paragraph(inline(' '.join(para)), S['body'])); para.clear()
    while i < len(lines):
        ln = lines[i].rstrip(); s = ln.strip()
        if not s:
            flush(); i += 1; continue
        if s.startswith('%%'):
            i += 1; continue
        if s.startswith('#! '):
            flush(); story.append(Spacer(1, 10)); story.append(Paragraph(inline(s[3:]), S['h1']))
            story.append(Table([['']], colWidths=[0.9 * inch], rowHeights=[3], style=[('BACKGROUND', (0, 0), (-1, -1), GOLD)]))
            story.append(Spacer(1, 10)); i += 1; continue
        if s.startswith('# '):
            flush()
            m = re.match(r'# (?:\[(.+?)\]\s*)?(.+)', s)
            story += [NextPageTemplate('chap'), PageBreak(), NextPageTemplate('main')]
            if m.group(1):
                story.append(Spacer(1, 18)); story.append(Paragraph(m.group(1).upper(), S['chapno']))
            else:
                story.append(Spacer(1, 18))
            story.append(heading(m.group(2), S['h1'], 0))
            story.append(Table([['']], colWidths=[0.9 * inch], rowHeights=[3],
                               style=[('BACKGROUND', (0, 0), (-1, -1), GOLD)]))
            story.append(Spacer(1, 10))
            i += 1; continue
        if s.startswith('## '):
            flush(); story.append(CondPageBreak(1.3 * inch)); story.append(heading(s[3:], S['h2'], 1)); i += 1; continue
        if s.startswith('### '):
            flush(); story.append(CondPageBreak(0.9 * inch)); story.append(Paragraph(inline(s[4:]), S['h3'])); i += 1; continue
        if s.startswith('LEAD:'):
            flush(); story.append(Paragraph(inline(s[5:].strip()), S['lead'])); i += 1; continue
        if s == '---page':
            flush(); story.append(PageBreak()); i += 1; continue
        m = re.match(r'!(TIP|WARN|NOTE|WHY|TRY)\s+(.*)', s)
        if m:
            flush(); story += callout(m.group(1), m.group(2)); i += 1; continue
        if s.startswith('!SAY '):
            flush(); story += say_box(s[5:]); i += 1; continue
        if s.startswith('SW|'):
            flush(); data = []
            while i < len(lines) and lines[i].strip().startswith('SW|'):
                p = lines[i].strip().split('|')
                data.append(['', Paragraph('<b>' + inline(p[2]) + '</b>', S['cell']), Paragraph(inline(p[3]), S['cell'])])
                i += 1
            t = Table(data, colWidths=[0.55 * inch, 1.15 * inch, CW - 1.7 * inch])
            st = [('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LINEBELOW', (0, 0), (-1, -1), 0.4, colors.HexColor('#D8D0C0')),
                  ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]
            for k, ln2 in enumerate(data):
                pass
            j = i - len(data)
            for k in range(len(data)):
                hx = lines[j + k].strip().split('|')[1]
                st.append(('BACKGROUND', (0, k), (0, k), colors.HexColor(hx)))
            t.setStyle(TableStyle(st)); story += [Spacer(1, 3), t, Spacer(1, 9)]; continue
        if s.startswith('WR|'):
            flush(); p = s.split('|'); story += wr_box(p[1], p[2], p[3]); i += 1; continue
        if s.startswith('|'):
            flush(); rows = []; widths = None
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if cells and cells[0].startswith('W='):
                    fr = [float(x) for x in cells[0][2:].split(',')]; widths = [CW * x / sum(fr) for x in fr]
                    cells = cells[1:]
                if not all(re.fullmatch(r':?-+:?', c) for c in cells):
                    rows.append(cells)
                i += 1
            story += table(rows, widths); continue
        if s.startswith('[ ] '):
            flush(); story.append(Paragraph(inline(s[4:]), S['chk'], bulletText='☐')); i += 1; continue
        if s.startswith('- '):
            flush(); story.append(Paragraph(inline(s[2:]), S['bul'], bulletText='•')); i += 1; continue
        m = re.match(r'(\d+)\. (.*)', s)
        if m:
            flush(); story.append(Paragraph(inline(m.group(2)), S['num'], bulletText=m.group(1) + '.')); i += 1; continue
        para.append(s); i += 1
    flush()


def build():
    story = [NextPageTemplate('plain'), PageBreak()]
    # Thank-you / intro page
    parse('content/00_intro.txt', story)
    story += [NextPageTemplate('plain'), PageBreak(), Spacer(1, 10),
              Paragraph('Contents', S['h1']),
              Table([['']], colWidths=[0.9 * inch], rowHeights=[3], style=[('BACKGROUND', (0, 0), (-1, -1), GOLD)]),
              Spacer(1, 12)]
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle('t0', fontName='Sans-B', fontSize=10.5, leading=14, leftIndent=0, spaceBefore=6, textColor=NAVY),
                       ParagraphStyle('t1', fontName='Serif', fontSize=9.4, leading=12.2, leftIndent=14, textColor=GREY)]
    toc.dotsMinLevel = 0
    story.append(toc)
    files = sorted(f for f in glob.glob('content/*.txt') if not f.endswith('00_intro.txt'))
    first = True
    for f in files:
        sub = []; parse(f, sub)
        if first:
            # the TOC page break: first chapter header already inserts a page break
            first = False
        story += sub
    doc = Doc('out/The_Over-60_Fit_and_Style_Guide.pdf')
    doc.multiBuild(story)
    return doc


if __name__ == '__main__':
    os.makedirs('out', exist_ok=True)
    d = build()
    print('pages:', d.page)
