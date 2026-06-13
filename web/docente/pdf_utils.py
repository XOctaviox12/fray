# docente/pdf_utils.py
# ─────────────────────────────────────────────────────────────────────────────
# Utilidades para generar PDFs con ReportLab
# ─────────────────────────────────────────────────────────────────────────────
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.utils import timezone

# ── Paleta de colores FRAY ────────────────────────────────────────────────────
AZUL_OSCURO  = colors.HexColor('#10131c')
AZUL_ACCENT  = colors.HexColor('#4f6ef7')
VERDE_OK     = colors.HexColor('#10b981')
ROJO_DANGER  = colors.HexColor('#e53e3e')
AMARILLO     = colors.HexColor('#f59e0b')
GRIS_BORDE   = colors.HexColor('#e8eaf0')
GRIS_BG      = colors.HexColor('#f4f5f9')
BLANCO       = colors.white
NEGRO        = colors.HexColor('#111318')
GRIS_TEXTO   = colors.HexColor('#6b7280')


def _color_nota(nota):
    if nota is None:
        return GRIS_TEXTO
    if nota >= 7:
        return VERDE_OK
    if nota >= 6:
        return AMARILLO
    return ROJO_DANGER


def _header_footer(canvas, doc, titulo, subtitulo, plantel_nombre):
    """Dibuja encabezado y pie de página en cada hoja."""
    canvas.saveState()
    w, h = doc.pagesize

    # Banda superior
    canvas.setFillColor(AZUL_OSCURO)
    canvas.rect(0, h - 52, w, 52, fill=1, stroke=0)

    # Logo / nombre sistema
    canvas.setFillColor(AZUL_ACCENT)
    canvas.roundRect(18, h - 40, 26, 26, 4, fill=1, stroke=0)
    canvas.setFillColor(BLANCO)
    canvas.setFont('Helvetica-Bold', 11)
    canvas.drawString(25, h - 28, 'F')

    # Título
    canvas.setFont('Helvetica-Bold', 12)
    canvas.setFillColor(BLANCO)
    canvas.drawString(52, h - 26, titulo)

    # Subtítulo
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.HexColor('#9ca3af'))
    canvas.drawString(52, h - 40, subtitulo)

    # Plantel (derecha)
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.HexColor('#9ca3af'))
    canvas.drawRightString(w - 18, h - 26, plantel_nombre)

    # Fecha generación
    fecha = timezone.now().strftime('%d/%m/%Y %H:%M')
    canvas.drawRightString(w - 18, h - 40, f'Generado: {fecha}')

    # Pie de página
    canvas.setFillColor(GRIS_BG)
    canvas.rect(0, 0, w, 28, fill=1, stroke=0)
    canvas.setFillColor(GRIS_TEXTO)
    canvas.setFont('Helvetica', 8)
    canvas.drawString(18, 10, 'FRAY · Sistema Educativo — Kronerion Design S.A.S. de C.V.')
    canvas.drawRightString(w - 18, 10, f'Pág. {doc.page}')

    canvas.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# PDF 1: BOLETA INDIVIDUAL POR GRUPO
# ─────────────────────────────────────────────────────────────────────────────
def generar_pdf_boleta(grupo, asignaturas, filas, docente):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=2.2*cm, bottomMargin=1.5*cm,
    )

    plantel_nombre = docente.plantel.nombre if docente.plantel else 'FRAY'
    titulo    = f'Boleta de Calificaciones — {grupo}'
    subtitulo = f'Docente: {docente.get_full_name()}'

    styles = getSampleStyleSheet()
    story  = []

    # Título visible en el documento
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f'<font size="14"><b>Boleta de Calificaciones</b></font>',
        ParagraphStyle('t', alignment=TA_LEFT, textColor=NEGRO, fontName='Helvetica-Bold', fontSize=14)
    ))
    story.append(Paragraph(
        f'Grupo: <b>{grupo}</b> &nbsp;&nbsp; Docente: <b>{docente.get_full_name()}</b>',
        ParagraphStyle('s', alignment=TA_LEFT, textColor=GRIS_TEXTO, fontSize=9, spaceAfter=6)
    ))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GRIS_BORDE, spaceAfter=10))

    # Tabla
    col_alumno   = [5*cm]
    col_asigs    = [3.2*cm] * len(asignaturas)
    col_promedio = [2.5*cm]
    col_widths   = col_alumno + col_asigs + col_promedio

    # Cabecera
    header_row = ['Alumno'] + [a.nombre for a in asignaturas] + ['Promedio']
    data = [header_row]

    for fila in filas:
        alumno = fila['alumno']
        row = [alumno.get_full_name()]
        for col in fila['cols']:
            nota = col.get('final')
            row.append(f'{nota:.1f}' if nota is not None else '—')

        # Promedio general
        notas = [c.get('final') for c in fila['cols'] if c.get('final') is not None]
        prom = round(sum(notas)/len(notas), 1) if notas else None
        row.append(f'{prom:.1f}' if prom is not None else '—')
        data.append(row)

    table = Table(data, colWidths=col_widths, repeatRows=1)

    # Estilo base
    ts = TableStyle([
        # Cabecera
        ('BACKGROUND',    (0, 0), (-1, 0), AZUL_OSCURO),
        ('TEXTCOLOR',     (0, 0), (-1, 0), BLANCO),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 8),
        ('ALIGN',         (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, 0), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        # Filas de datos
        ('FONTSIZE',      (0, 1), (-1, -1), 8.5),
        ('ALIGN',         (1, 1), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 1), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BLANCO, GRIS_BG]),
        ('GRID',          (0, 0), (-1, -1), 0.4, GRIS_BORDE),
        # Columna promedio resaltada
        ('BACKGROUND',    (-1, 0), (-1, -1), colors.HexColor('#eef0fe')),
        ('FONTNAME',      (-1, 1), (-1, -1), 'Helvetica-Bold'),
    ])

    # Color por nota
    for row_idx, fila in enumerate(filas, start=1):
        notas = [c.get('final') for c in fila['cols'] if c.get('final') is not None]
        prom = round(sum(notas)/len(notas), 1) if notas else None
        color = _color_nota(prom)
        ts.add('TEXTCOLOR', (-1, row_idx), (-1, row_idx), color)

        for col_idx, col in enumerate(fila['cols'], start=1):
            nota = col.get('final')
            ts.add('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), _color_nota(nota))

    table.setStyle(ts)
    story.append(table)

    # Leyenda
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        '<font color="#10b981">■</font> ≥ 7.0 Aprobado &nbsp;&nbsp; '
        '<font color="#f59e0b">■</font> 6.0–6.9 Suficiente &nbsp;&nbsp; '
        '<font color="#e53e3e">■</font> &lt; 6.0 Reprobado',
        ParagraphStyle('leg', fontSize=8, textColor=GRIS_TEXTO)
    ))

    doc.build(
        story,
        onFirstPage=lambda c, d: _header_footer(c, d, titulo, subtitulo, plantel_nombre),
        onLaterPages=lambda c, d: _header_footer(c, d, titulo, subtitulo, plantel_nombre),
    )
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────────────────────────────────────
# PDF 2: CONCENTRADO DE CALIFICACIONES
# ─────────────────────────────────────────────────────────────────────────────
def generar_pdf_concentrado(grupo, asignaturas, filas, docente):
    """Igual que boleta pero con columnas de tareas, actividades y manual."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=2.2*cm, bottomMargin=1.5*cm,
    )

    plantel_nombre = docente.plantel.nombre if docente.plantel else 'FRAY'
    titulo    = f'Concentrado de Calificaciones — {grupo}'
    subtitulo = f'Docente: {docente.get_full_name()}'

    story = []
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        '<font size="14"><b>Concentrado de Calificaciones</b></font>',
        ParagraphStyle('t', alignment=TA_LEFT, textColor=NEGRO, fontName='Helvetica-Bold', fontSize=14)
    ))
    story.append(Paragraph(
        f'Grupo: <b>{grupo}</b> &nbsp;&nbsp; Docente: <b>{docente.get_full_name()}</b>',
        ParagraphStyle('s', alignment=TA_LEFT, textColor=GRIS_TEXTO, fontSize=9, spaceAfter=6)
    ))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GRIS_BORDE, spaceAfter=10))

    col_widths = [4.5*cm] + [2*cm] * len(asignaturas) + [2.5*cm]
    header = ['Alumno'] + [a.nombre for a in asignaturas] + ['Promedio']
    data = [header]

    for fila in filas:
        row = [fila['alumno'].get_full_name()]
        for nota in fila['cols']:
            row.append(f'{nota:.1f}' if nota is not None else '—')
        prom = fila.get('promedio_general')
        row.append(f'{prom:.1f}' if prom is not None else '—')
        data.append(row)

    table = Table(data, colWidths=col_widths, repeatRows=1)
    ts = TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), AZUL_OSCURO),
        ('TEXTCOLOR',     (0, 0), (-1, 0), BLANCO),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 8),
        ('ALIGN',         (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, 0), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('FONTSIZE',      (0, 1), (-1, -1), 8.5),
        ('ALIGN',         (1, 1), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 1), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BLANCO, GRIS_BG]),
        ('GRID',          (0, 0), (-1, -1), 0.4, GRIS_BORDE),
        ('BACKGROUND',    (-1, 0), (-1, -1), colors.HexColor('#eef0fe')),
        ('FONTNAME',      (-1, 1), (-1, -1), 'Helvetica-Bold'),
    ])

    for row_idx, fila in enumerate(filas, start=1):
        prom = fila.get('promedio_general')
        ts.add('TEXTCOLOR', (-1, row_idx), (-1, row_idx), _color_nota(prom))
        for col_idx, nota in enumerate(fila['cols'], start=1):
            ts.add('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), _color_nota(nota))

    table.setStyle(ts)
    story.append(table)

    doc.build(
        story,
        onFirstPage=lambda c, d: _header_footer(c, d, titulo, subtitulo, plantel_nombre),
        onLaterPages=lambda c, d: _header_footer(c, d, titulo, subtitulo, plantel_nombre),
    )
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────────────────────────────────────
# PDF 3: REPORTE DE ASISTENCIA MENSUAL
# ─────────────────────────────────────────────────────────────────────────────
def generar_pdf_asistencia(grupo, asignatura, filas, fecha, docente):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=2.2*cm, bottomMargin=1.5*cm,
    )

    plantel_nombre = docente.plantel.nombre if docente.plantel else 'FRAY'
    mes_año = fecha.strftime('%B %Y').capitalize()
    titulo    = f'Reporte de Asistencia — {mes_año}'
    subtitulo = f'{grupo} · {asignatura}'

    story = []
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f'<font size="14"><b>Reporte de Asistencia</b></font>',
        ParagraphStyle('t', alignment=TA_LEFT, textColor=NEGRO, fontName='Helvetica-Bold', fontSize=14)
    ))
    story.append(Paragraph(
        f'Grupo: <b>{grupo}</b> &nbsp; Materia: <b>{asignatura}</b> &nbsp; Mes: <b>{mes_año}</b>',
        ParagraphStyle('s', alignment=TA_LEFT, textColor=GRIS_TEXTO, fontSize=9, spaceAfter=6)
    ))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GRIS_BORDE, spaceAfter=10))

    col_widths = [5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm]
    header = ['Alumno', 'Presentes', 'Retardos', 'Ausencias', '% Asist.']
    data = [header]

    for fila in filas:
        alumno   = fila['alumno']
        p = fila.get('presentes', 0)
        r = fila.get('retardos', 0)
        a = fila.get('ausentes', 0)
        total = p + r + a
        pct = round((p / total) * 100) if total > 0 else 0
        data.append([
            alumno.get_full_name(),
            str(p), str(r), str(a),
            f'{pct}%',
        ])

    table = Table(data, colWidths=col_widths, repeatRows=1)
    ts = TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), AZUL_OSCURO),
        ('TEXTCOLOR',     (0, 0), (-1, 0), BLANCO),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 9),
        ('ALIGN',         (1, 0), (-1, 0), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, 0), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('FONTSIZE',      (0, 1), (-1, -1), 9),
        ('ALIGN',         (1, 1), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 1), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BLANCO, GRIS_BG]),
        ('GRID',          (0, 0), (-1, -1), 0.4, GRIS_BORDE),
        # Columna % resaltada
        ('BACKGROUND',    (-1, 0), (-1, -1), colors.HexColor('#eef0fe')),
        ('FONTNAME',      (-1, 1), (-1, -1), 'Helvetica-Bold'),
    ])

    for row_idx, fila in enumerate(filas, start=1):
        p = fila.get('presentes', 0)
        r = fila.get('retardos', 0)
        a = fila.get('ausentes', 0)
        total = p + r + a
        pct = round((p / total) * 100) if total > 0 else 0
        color = VERDE_OK if pct >= 80 else (AMARILLO if pct >= 60 else ROJO_DANGER)
        ts.add('TEXTCOLOR', (-1, row_idx), (-1, row_idx), color)

    table.setStyle(ts)
    story.append(table)

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        '<font color="#10b981">■</font> ≥ 80% Buena asistencia &nbsp;&nbsp; '
        '<font color="#f59e0b">■</font> 60–79% Regular &nbsp;&nbsp; '
        '<font color="#e53e3e">■</font> &lt; 60% Crítico',
        ParagraphStyle('leg', fontSize=8, textColor=GRIS_TEXTO)
    ))

    doc.build(
        story,
        onFirstPage=lambda c, d: _header_footer(c, d, titulo, subtitulo, plantel_nombre),
        onLaterPages=lambda c, d: _header_footer(c, d, titulo, subtitulo, plantel_nombre),
    )
    buffer.seek(0)
    return buffer