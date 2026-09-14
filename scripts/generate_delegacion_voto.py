from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "public" / "documentos" / "delegacion-de-voto-puerta-europa.pdf"

pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))

INK = colors.HexColor("#273750")
TEAL = colors.HexColor("#247D75")
LAVENDER = colors.HexColor("#DCD9F2")
CREAM = colors.HexColor("#FFF9F0")
LINE = colors.HexColor("#BFC8C3")


def field_line(label: str, width: str = "") -> Paragraph:
    suffix = f" {width}" if width else " ________________________________________________"
    return Paragraph(f"<b>{label}</b>{suffix}", styles["Field"])


def add_metadata(canvas, doc):
    canvas.saveState()
    canvas.setTitle("Delegación de representación y voto - Puerta Europa")
    canvas.setAuthor("Comisión de Vecinos de Puerta Europa")
    canvas.setSubject("Modelo de delegación para Junta de Propietarios")
    canvas.setFont("Arial", 8)
    canvas.setFillColor(colors.HexColor("#6C7470"))
    canvas.drawCentredString(A4[0] / 2, 10 * mm, "Comunidad de Propietarios Puerta Europa")
    canvas.restoreState()


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="TitlePE",
        fontName="Arial-Bold",
        fontSize=20,
        leading=24,
        textColor=INK,
        alignment=TA_CENTER,
        spaceAfter=4 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="SubtitlePE",
        fontName="Arial-Bold",
        fontSize=9,
        leading=12,
        textColor=TEAL,
        alignment=TA_CENTER,
        spaceAfter=5 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="BodyPE",
        fontName="Arial",
        fontSize=9.3,
        leading=13,
        textColor=INK,
        alignment=TA_LEFT,
        spaceAfter=2.2 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="Field",
        fontName="Arial",
        fontSize=9.5,
        leading=14,
        textColor=INK,
        spaceAfter=2.2 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="SmallPE",
        fontName="Arial",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#5F6965"),
    )
)
styles.add(
    ParagraphStyle(
        name="TableHeadPE",
        fontName="Arial-Bold",
        fontSize=7.5,
        leading=9,
        textColor=INK,
        alignment=TA_CENTER,
    )
)
styles.add(
    ParagraphStyle(
        name="TableCellPE",
        fontName="Arial",
        fontSize=7.5,
        leading=9.5,
        textColor=INK,
    )
)

doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    rightMargin=18 * mm,
    leftMargin=18 * mm,
    topMargin=15 * mm,
    bottomMargin=17 * mm,
)

story = [
    Paragraph("DELEGACIÓN DE REPRESENTACIÓN Y VOTO", styles["TitlePE"]),
    Paragraph("JUNTA DE PROPIETARIOS - PUERTA EUROPA", styles["SubtitlePE"]),
    HRFlowable(width="100%", thickness=1.2, color=TEAL, spaceAfter=4 * mm),
    field_line("Junta convocada para el día:"),
    field_line("Lugar y hora:"),
    Spacer(1, 1.5 * mm),
    Paragraph("DATOS DE LA PERSONA PROPIETARIA", styles["SubtitlePE"]),
    field_line("D./D.ª:"),
    field_line("Vivienda/local y portal:"),
    Spacer(1, 1.5 * mm),
    Paragraph("PERSONA REPRESENTANTE", styles["SubtitlePE"]),
    field_line("D./D.ª:"),
    Spacer(1, 1.5 * mm),
    Paragraph(
        "Por medio del presente escrito delego mi representación y voto en la persona indicada para la Junta de Propietarios señalada, con facultad para intervenir y votar en mi nombre. Esta delegación se limita a dicha Junta.",
        styles["BodyPE"],
    ),
    Paragraph(
        "Si desea fijar instrucciones para las propuestas del aviso 3, marque una sola casilla por fila. Si no marca ninguna opción, la persona representante votará según su criterio.",
        styles["BodyPE"],
    ),
]

head = [
    Paragraph("N.º", styles["TableHeadPE"]),
    Paragraph("Propuesta", styles["TableHeadPE"]),
    Paragraph("A favor", styles["TableHeadPE"]),
    Paragraph("En contra", styles["TableHeadPE"]),
    Paragraph("Abstención", styles["TableHeadPE"]),
    Paragraph("Criterio del representante", styles["TableHeadPE"]),
]
rows = [
    ["1", "Zona privada y uso comercial"],
    ["2", "Uso y paso; conservación y daños"],
    ["3", "Anteproyecto arquitectónico"],
    ["4", "Comisión e información"],
]
table_data = [head]
for number, title in rows:
    table_data.append(
        [
            Paragraph(number, styles["TableHeadPE"]),
            Paragraph(title, styles["TableCellPE"]),
            Paragraph("☐", styles["TableHeadPE"]),
            Paragraph("☐", styles["TableHeadPE"]),
            Paragraph("☐", styles["TableHeadPE"]),
            Paragraph("☐", styles["TableHeadPE"]),
        ]
    )

vote_table = Table(
    table_data,
    colWidths=[10 * mm, 56 * mm, 22 * mm, 22 * mm, 24 * mm, 36 * mm],
    rowHeights=[12 * mm, 13 * mm, 13 * mm, 13 * mm, 13 * mm],
    repeatRows=1,
)
vote_table.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), LAVENDER),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.6, LINE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (2, 1), (-1, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )
)
story.extend(
    [
        vote_table,
        Spacer(1, 4 * mm),
        Paragraph("OTRAS INSTRUCCIONES DE VOTO", styles["SubtitlePE"]),
        Paragraph("________________________________________________________________________________", styles["Field"]),
        Paragraph("________________________________________________________________________________", styles["Field"]),
        Spacer(1, 2 * mm),
        field_line("En:", "__________________________   <b>a:</b> ______ / ______ / __________"),
        Spacer(1, 7 * mm),
        Paragraph("Firma de la persona propietaria: __________________________________________", styles["Field"]),
        Spacer(1, 4 * mm),
        Table(
            [[Paragraph(
                "La Ley de Propiedad Horizontal permite la representación voluntaria mediante escrito firmado por la persona propietaria (art. 15.1). Entregue este documento según las indicaciones de la convocatoria y antes del inicio de la Junta.",
                styles["SmallPE"],
            )]],
            colWidths=[170 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), CREAM),
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#E6D7B9")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            ),
        ),
    ]
)

doc.build(story, onFirstPage=add_metadata, onLaterPages=add_metadata)
print(OUTPUT)
