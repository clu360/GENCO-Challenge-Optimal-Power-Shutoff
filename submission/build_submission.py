"""Build all publication figures and a three-page PDF using only adjacent files.

Install the repository's [paper] extra, then run python submission/build_submission.py.
Also works from an extracted submission packet with numpy/pandas/matplotlib/reportlab/pypdf.
This is results reproduction; no inference, training, AC solves, or network calls occur.
"""
from __future__ import annotations

import argparse
from functools import partial
import hashlib
import html
from io import BytesIO
import json
from pathlib import Path
import re
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / 'data'
FIG = HERE / 'figures'
NAVY = '#153148'
COLORS = ['#64758a', '#168585', '#ce7935', '#7860a0']


def check_data():
    manifest = json.loads((DATA / 'provenance.json').read_text(encoding='utf-8'))
    for name, entry in manifest['exports'].items():
        if hashlib.sha256((DATA / name).read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Publication input checksum mismatch: ' + name)
    return manifest


def save(fig, name):
    fig.savefig(FIG / (name + '.png'), dpi=240, facecolor='white', bbox_inches='tight')
    fig.savefig(FIG / (name + '.pdf'), facecolor='white', bbox_inches='tight',
                metadata={'CreationDate': None, 'ModDate': None})
    plt.close(fig)


def figures():
    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
        'axes.labelsize': 10, 'axes.titlesize': 11, 'axes.titleweight': 'bold',
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#b7c3cc',
        'axes.labelcolor': NAVY, 'text.color': NAVY, 'xtick.color': '#485d6d',
        'ytick.color': '#485d6d', 'legend.frameon': False, 'pdf.fonttype': 42})
    fig, ax = plt.subplots(figsize=(10.5, 1.52))
    ax.set(xlim=(0, 10.5), ylim=(0, 1.52)); ax.axis('off')
    labels = [('Adapt released GENCO\nG / random / wildfire', '#eaf0f5'),
              ('Propose topologies\nand load controls', '#eaf0f5'),
              ('GENCO state prediction\nBounded screening', '#e6f4f1'),
              ('Selected decisions\nExact AC audits A / B', '#e6f4f1')]
    for i, (label, color) in enumerate(labels):
        x = .03 + i * 2.65
        ax.add_patch(FancyBboxPatch((x, .75), 2.34, .65,
            boxstyle='round,pad=.025,rounding_size=.06', facecolor=color, edgecolor='#c5d2dc'))
        ax.text(x+1.17, 1.075, label, ha='center', va='center', fontsize=10)
        if i < 3:
            ax.annotate('', xy=(x+2.61, 1.075), xytext=(x+2.37, 1.075),
                        arrowprops={'arrowstyle': '->', 'color': '#6b7f8c', 'lw': 1.3})
    ax.text(.03, .4, 'COMPLETED', fontsize=8.8, color='#168585', weight='bold')
    ax.text(1.22, .4, 'Compare adaptation, physical fidelity, and selected AC outcomes', fontsize=9.5)
    ax.text(.03, .07, 'PROPOSED', fontsize=8.8, color='#b45e29', weight='bold')
    ax.text(1.22, .07, 'Broader screening  →  shortlist  →  risk-aware AC refinement  →  rerank', fontsize=9.5)
    save(fig, '01_workflow')

    validation = pd.read_csv(DATA / 'texas_validation.csv')
    exact = pd.read_csv(DATA / 'texas_selected_ac.csv')
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 2.65), gridspec_kw={'width_ratios': [1, 1.2]})
    models = ['G500', 'G→R', 'G→W']
    p = validation.pivot(index='model', columns='distribution', values='mean_bus_abs_p_mw').loc[models, ['G', 'R', 'W']]
    q = validation.pivot(index='model', columns='distribution', values='mean_bus_abs_q_mvar').loc[models, ['G', 'R', 'W']]
    axes[0].imshow(p, cmap='YlGnBu', vmin=48, vmax=62, aspect='auto')
    axes[0].set_xticks(range(3), ['G validation', 'R validation', 'W validation'], fontsize=9)
    axes[0].set_yticks(range(3), models)
    axes[0].tick_params(length=0)
    axes[0].spines[['left', 'bottom']].set_visible(False)
    axes[0].set_title('a  Mean P / Q imbalance', pad=10)
    for i in range(3):
        for j in range(3):
            axes[0].text(j, i, f'{p.iloc[i,j]:.1f} / {q.iloc[i,j]:.1f}', ha='center', va='center',
                         color='white' if p.iloc[i,j] > 55 else NAVY, fontsize=10.5)
    axes[1].axis('off'); axes[1].set_title('b  Native and AC scores disagree', pad=10)
    order = ['GENCO G500', 'GENCO G100 -> R400', 'GENCO G100 -> W400']
    rows = []
    for name, label in zip(order, models):
        r = exact[exact.model.eq(name)].iloc[0]
        rows.append([label, f'{r.native_j:.4f}', f'{r.a_j:.4f}', f'{r.a_r:.4f}', f'{100*r.shed:.3f}'])
    table = axes[1].table(cellText=rows,
        colLabels=['Model', 'Native J', 'AC Jᴬ', 'AC risk', 'Shed (%)'],
        cellLoc='center', colLoc='center', loc='center', colWidths=[.17, .21, .21, .21, .20])
    table.auto_set_font_size(False); table.set_fontsize(9.4); table.scale(1, 2.15)
    for (i, j), cell in table.get_celld().items():
        cell.set_edgecolor('white')
        cell.set_facecolor('#eaf0f5' if i == 0 else '#f4f8fa' if i % 2 else '#e6f4f1')
        cell.set_text_props(color=NAVY, weight='bold' if i == 0 else 'normal')
    # Emphasize G500's native advantage and both sequential models' audited advantage.
    for key in [(1, 1), (2, 2), (3, 2)]:
        table[key].set_text_props(color='#10786f', weight='bold')
    axes[1].text(.5, .02, 'Own selected decisions; all audited risks remain above baseline 1.',
                 transform=axes[1].transAxes, ha='center', fontsize=9)
    fig.tight_layout(w_pad=2.2)
    save(fig, '02_texas_evidence')

    agreement = pd.read_csv(DATA / 'goc_agreement.csv')
    metrics = ['mean_state_nrmse', 'mean_abs_risk_discrepancy', 'mean_abs_objective_discrepancy']
    relative = agreement[metrics].to_numpy() / agreement[metrics].iloc[0].to_numpy()
    runtime = json.loads((DATA / 'goc_runtime.json').read_text())
    times = {r['metric']: r['median'] for r in runtime['timing_summary']}
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 2.5), gridspec_kw={'width_ratios': [1.2, 1]})
    axes[0].imshow(relative, cmap='YlGnBu_r', vmin=0, vmax=1, aspect='auto')
    axes[0].set_xticks(range(3), ['State NRMSE', 'Risk discrepancy', 'J discrepancy'], fontsize=9)
    axes[0].set_yticks(range(4), agreement.model)
    axes[0].set_title('a  Error relative to M0 (lower is better)', pad=10)
    axes[0].tick_params(length=0); axes[0].spines[['left', 'bottom']].set_visible(False)
    for i in range(4):
        for j in range(3):
            axes[0].text(j, i, f'{relative[i,j]:.2f}', ha='center', va='center',
                         color='white' if relative[i,j] < .4 else NAVY, fontsize=11)
    values = [times['m0_evaluator_total'], times['refa_evaluator_total']]
    axes[1].barh(['GridSFM M0', 'Fixed-decision AC'], values, color=['#168585', '#64758a'], height=.5)
    axes[1].invert_yaxis()
    axes[1].set(xlabel='Median state-evaluation time (s)', xlim=(0, 1.38),
                title='b  Paired CPU benchmark: 54 decisions')
    for i, value in enumerate(values):
        axes[1].text(value+.025, i, f'{value:.3f} s', va='center', fontsize=10)
    fig.tight_layout(w_pad=2.7)
    save(fig, '03_goc_evidence')


def inline(text):
    text = html.escape(text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
        lambda m: '<link href="'+html.escape(m[2], quote=True)+'" color="#157f82">'+m[1]+'</link>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    return re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', text)


def pdf_build(pdf_tools=None):
    if pdf_tools:
        sys.path.insert(0, str(Path(pdf_tools).resolve()))
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer, PageBreak
    from PIL import Image as PILImage
    from pypdf import PdfReader

    # Bundle-independent fallback from matplotlib's installed font assets.
    for name, weight, style in [('Body', 'normal', 'normal'), ('BodyBold', 'bold', 'normal'),
                                ('BodyItalic', 'normal', 'italic'), ('BodyBoldItalic', 'bold', 'italic')]:
        path = font_manager.findfont(font_manager.FontProperties(family='DejaVu Sans', weight=weight, style=style))
        pdfmetrics.registerFont(TTFont(name, path))
    pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold', italic='BodyItalic', boldItalic='BodyBoldItalic')
    styles = {
        'title': ParagraphStyle('title', fontName='BodyBold', fontSize=23, leading=26,
            textColor=colors.HexColor(NAVY), spaceAfter=8),
        'h2': ParagraphStyle('h2', fontName='BodyBold', fontSize=11.5, leading=14,
            textColor=colors.HexColor(NAVY), spaceBefore=7, spaceAfter=5, keepWithNext=True),
        'body': ParagraphStyle('body', fontName='Body', fontSize=9.3, leading=12,
            textColor=colors.HexColor('#223b4d'), spaceAfter=7),
        'caption': ParagraphStyle('caption', fontName='Body', fontSize=8, leading=10,
            textColor=colors.HexColor('#526675'), spaceAfter=7),
        'resources': ParagraphStyle('resources', fontName='Body', fontSize=7.7, leading=9.5,
            textColor=colors.HexColor('#526675'), spaceAfter=5)}
    output = HERE / 'GENCO_Challenge_Submission.pdf'
    doc = SimpleDocTemplate(str(output), pagesize=(612, 792), rightMargin=38, leftMargin=38,
        topMargin=37, bottomMargin=36, title='GENCO in the Loop', author='Caleb Lu; Xiao Liu',
        subject='Grid-to-task adaptation and physical verification for wildfire-aware power shutoff')
    markdown = (HERE / 'SUBMISSION.md').read_text(encoding='utf-8')
    story = []
    local_links = []
    for block in re.split(r'\n\s*\n', markdown.strip()):
        if block.strip() == '<!-- pagebreak -->':
            story.append(PageBreak()); continue
        if block.startswith('# '):
            story.append(Paragraph(inline(block[2:]), styles['title'])); continue
        if block.startswith('## '):
            story.append(Paragraph(inline(block[3:]), styles['h2'])); continue
        match = re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)', block.strip())
        if match:
            path = HERE / match[2]
            with PILImage.open(path) as im:
                w, h = im.size
            story.append(Image(BytesIO(path.read_bytes()), width=doc.width, height=doc.width*h/w))
            story.append(Spacer(1, 3)); continue
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', block):
            if '://' not in target and not target.startswith('mailto:'):
                local_links.append(target)
        style = 'caption' if block.startswith('*Figure ') else 'resources' if block.startswith(('**Resources.', '**References.')) else 'body'
        story.append(Paragraph(inline(block).replace('  \n', '<br/>').replace('\n', ' '), styles[style]))

    def decorate(canvas, document):
        canvas.saveState(); canvas.setStrokeColor(colors.HexColor('#d4dfe6'))
        canvas.line(38, 28, 574, 28); canvas.setFont('Body', 7.5)
        canvas.setFillColor(colors.HexColor('#607582'))
        canvas.drawString(38, 16, 'GENCO Challenge 2026  |  Caleb Lu · Xiao Liu')
        canvas.drawRightString(574, 16, str(document.page))
        if document.page > 1:
            canvas.drawString(38, 778, 'GENCO IN THE LOOP  |  ADAPTATION AND PHYSICAL VERIFICATION')
        canvas.restoreState()

    doc.build(story, onFirstPage=decorate, onLaterPages=decorate,
              canvasmaker=partial(Canvas, invariant=1))
    reader = PdfReader(output)
    verification = dict(pdf_pages=len(reader.pages),
        characters_by_page=[len(page.extract_text() or '') for page in reader.pages],
        embedded_images_by_page=[len(page.images) for page in reader.pages],
        missing_local_links=[p for p in local_links if not (HERE / p).is_file()],
        markdown_words=len(markdown.split()), pdf_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        data_provenance_sha256=hashlib.sha256((DATA / 'provenance.json').read_bytes()).hexdigest(),
        source_scope='Adjacent compact data only; no development checkout, private data, PACE, or model execution')
    (HERE / 'build_verification.json').write_text(json.dumps(verification, indent=2), encoding='utf-8')
    print(json.dumps(verification))
    if len(reader.pages) != 3 or verification['embedded_images_by_page'] != [1, 1, 1] or verification['missing_local_links']:
        raise RuntimeError('Publication layout or local links failed verification')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--figures-only', action='store_true')
    parser.add_argument('--pdf-only', action='store_true')
    parser.add_argument('--pdf-tools', help='Optional existing ReportLab/pypdf directory')
    args = parser.parse_args()
    inputs = check_data()
    if not args.pdf_only:
        figures()
        provenance = dict(inputs)
        provenance['figure_files'] = {
            p.relative_to(HERE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(FIG.iterdir()) if p.suffix in {'.png', '.pdf'}}
        (HERE / 'figure_provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    if not args.figures_only:
        pdf_build(args.pdf_tools)


if __name__ == '__main__':
    main()
