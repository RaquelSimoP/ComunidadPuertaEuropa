from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


SOURCE = Path(r"C:\Users\raque\Desktop\Terraza\JuntaSeptiembre2026\Plano_conjunto_Puerta_Europa.pdf")
WORK = Path("tmp/pdfs")
OUTPUT = Path("output/pdf/Plano_conjunto_Puerta_Europa_anonimizado.pdf")
CLEAN_PLAN = WORK / "plano-base-anonimizado.png"

PAGE_W = 1683.780029296875
PAGE_H = 1190.550048828125
PLAN_X = 63.0
PLAN_Y = 123.192138671875
PLAN_W = 1557.780029296875
PLAN_H = 941.35791015625

NAVY = (37, 57, 82)
TEAL = (24, 115, 110)
GREEN = (217, 238, 230)
GREEN_EDGE = (92, 154, 143)
YELLOW = (249, 237, 202)
YELLOW_EDGE = (222, 184, 92)
HATCH = (59, 129, 119)
ORANGE = (188, 93, 38)
MUTED = (93, 108, 111)


def close_mask(mask: Image.Image, size: int) -> Image.Image:
    radius = max(1.0, size / 4)
    blurred = np.asarray(mask.filter(ImageFilter.GaussianBlur(radius=radius)))
    return Image.fromarray(np.where(blurred > 72, 255, 0).astype(np.uint8), mode="L")


def erode_mask(mask: Image.Image, size: int) -> Image.Image:
    radius = max(1.0, size / 3)
    blurred = np.asarray(mask.filter(ImageFilter.GaussianBlur(radius=radius)))
    return Image.fromarray(np.where(blurred > 210, 255, 0).astype(np.uint8), mode="L")


def fill_holes(mask: Image.Image) -> Image.Image:
    inverted = ImageOps.invert(mask.convert("L"))
    ImageDraw.floodfill(inverted, (0, 0), 128, thresh=0)
    values = np.asarray(inverted)
    holes = values == 255
    result = np.asarray(mask).copy()
    result[holes] = 255
    return Image.fromarray(result.astype(np.uint8), mode="L")


def extract_and_simplify_plan() -> None:
    document = pymupdf.open(SOURCE)
    page = document[0]
    image_info = page.get_image_info(xrefs=True)
    if len(image_info) != 1:
        raise RuntimeError(f"Expected one embedded plan image, found {len(image_info)}")

    extracted = document.extract_image(image_info[0]["xref"])
    source = Image.open(BytesIO(extracted["image"])).convert("RGB")
    target_w = 3200
    target_h = round(target_w * source.height / source.width)
    source = source.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # A broad blur recovers the original colour fields beneath fine plan lines,
    # measurements and room labels. Only the colour geometry is retained.
    smooth = source.filter(ImageFilter.GaussianBlur(radius=10))
    pixels = np.asarray(smooth, dtype=np.int16)
    red, green, blue = pixels[..., 0], pixels[..., 1], pixels[..., 2]
    brightness = (red + green + blue) / 3

    green_raw = (
        (brightness > 178)
        & ((green - red) > 7)
        & ((blue - red) > 2)
        & ((green - blue) > 1)
    )
    yellow_raw = (
        (brightness > 178)
        & ((red - blue) > 18)
        & ((green - blue) > 10)
        & ~green_raw
    )

    green_mask = Image.fromarray((green_raw * 255).astype(np.uint8), mode="L")
    yellow_mask = Image.fromarray((yellow_raw * 255).astype(np.uint8), mode="L")
    green_mask = close_mask(green_mask, 17)
    yellow_mask = close_mask(yellow_mask, 17)
    green_mask = fill_holes(green_mask)
    yellow_mask = fill_holes(yellow_mask)

    cleaned = Image.new("RGB", source.size, "white")
    cleaned.paste(YELLOW, mask=yellow_mask)
    cleaned.paste(GREEN, mask=green_mask)

    # The soportal is shown schematically as the private strip touching the
    # central public-use area. The hatch is intentionally labelled orientative.
    public_blur = np.asarray(yellow_mask.filter(ImageFilter.GaussianBlur(radius=75)))
    near_public = Image.fromarray(np.where(public_blur > 2, 255, 0).astype(np.uint8), mode="L")
    soportal = Image.fromarray(
        np.minimum(np.asarray(green_mask), np.asarray(near_public)).astype(np.uint8),
        mode="L",
    )

    hatch_layer = Image.new("RGB", source.size, HATCH)
    hatch_alpha = Image.new("L", source.size, 0)
    hatch_draw = ImageDraw.Draw(hatch_alpha)
    spacing = 34
    for offset in range(-source.height, source.width + source.height, spacing):
        hatch_draw.line((offset, source.height, offset + source.height, 0), fill=105, width=3)
    hatch_alpha = Image.fromarray(
        np.minimum(np.asarray(hatch_alpha), np.asarray(soportal)).astype(np.uint8),
        mode="L",
    )
    cleaned.paste(hatch_layer, mask=hatch_alpha)

    # Retain only the boundaries of the colour fields, not the architectural
    # internals, room names, dimensions or technical symbols.
    green_inner = erode_mask(green_mask, 9)
    yellow_inner = erode_mask(yellow_mask, 9)
    green_edge = Image.fromarray(
        np.maximum(np.asarray(green_mask) - np.asarray(green_inner), 0).astype(np.uint8),
        mode="L",
    )
    yellow_edge = Image.fromarray(
        np.maximum(np.asarray(yellow_mask) - np.asarray(yellow_inner), 0).astype(np.uint8),
        mode="L",
    )
    cleaned.paste(YELLOW_EDGE, mask=yellow_edge)
    cleaned.paste(GREEN_EDGE, mask=green_edge)
    CLEAN_PLAN.parent.mkdir(parents=True, exist_ok=True)
    cleaned.save(CLEAN_PLAN, optimize=True)


def draw_hatched_swatch(pdf: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    pdf.setFillColorRGB(*(channel / 255 for channel in GREEN))
    pdf.roundRect(x, y, w, h, 5, stroke=0, fill=1)
    pdf.saveState()
    path = pdf.beginPath()
    path.roundRect(x, y, w, h, 5)
    pdf.clipPath(path, stroke=0, fill=0)
    pdf.setStrokeColorRGB(*(channel / 255 for channel in HATCH))
    pdf.setLineWidth(1.1)
    step = 9
    for offset in range(-int(h), int(w + h), step):
        pdf.line(x + offset, y, x + offset + h, y + h)
    pdf.restoreState()


def draw_label(pdf: canvas.Canvas, text: str, x: float, y: float, rotation: int = 0) -> None:
    pdf.saveState()
    pdf.translate(x, y)
    pdf.rotate(rotation)
    pdf.setFont("Helvetica-Bold", 11)
    width = stringWidth(text, "Helvetica-Bold", 11)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.roundRect(-5, -3, width + 10, 17, 3, stroke=0, fill=1)
    pdf.setFillColorRGB(*(channel / 255 for channel in NAVY))
    pdf.drawString(0, 1, text)
    pdf.restoreState()


def build_pdf() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(OUTPUT), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    pdf.setTitle("Plano anonimizado del soportal - Puerta Europa")
    pdf.setAuthor("Comisión de Vecinos - Puerta Europa")
    pdf.setSubject("Figura esquemática anonimizada; sin cotas ni datos internos")

    pdf.setFillColorRGB(1, 1, 1)
    pdf.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    pdf.drawImage(str(CLEAN_PLAN), PLAN_X, PLAN_Y, width=PLAN_W, height=PLAN_H, preserveAspectRatio=True, mask="auto")

    pdf.setFillColorRGB(*(channel / 255 for channel in TEAL))
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(48, PAGE_H - 42, "PUERTA EUROPA")
    pdf.setFillColorRGB(*(channel / 255 for channel in NAVY))
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawString(48, PAGE_H - 79, "Plano anonimizado del soportal")
    pdf.setFont("Helvetica", 13)
    pdf.drawString(48, PAGE_H - 103, "Esquema de zonas - sin cotas, estancias ni datos internos")

    pdf.setFillColorRGB(*(channel / 255 for channel in ORANGE))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawRightString(PAGE_W - 48, PAGE_H - 43, "FIGURA ESQUEMÁTICA - 15.09.2026")
    pdf.setFillColorRGB(*(channel / 255 for channel in MUTED))
    pdf.setFont("Helvetica", 10)
    pdf.drawRightString(PAGE_W - 48, PAGE_H - 63, "Sin escala de medición")

    # Central legend placed over the open courtyard so the block geometry remains visible.
    box_x, box_y, box_w, box_h = 505, 640, 675, 252
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setStrokeColorRGB(0.87, 0.88, 0.86)
    pdf.setLineWidth(0.8)
    pdf.roundRect(box_x, box_y, box_w, box_h, 13, stroke=1, fill=1)
    pdf.setFillColorRGB(*(channel / 255 for channel in NAVY))
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(box_x + 28, box_y + box_h - 38, "Cómo leer el plano")

    legend = [
        ("private", "ZONA PRIVADA", "Edificación y suelo privado representados de forma esquemática."),
        ("soportal", "SOPORTAL - ZONA PRIVADA RAYADA", "Franja orientativa junto al espacio central; requiere comprobación técnica."),
        ("public", "ZONA DE USO PÚBLICO", "El color expresa el uso y no certifica por sí solo la titularidad municipal."),
    ]
    row_y = box_y + box_h - 88
    for kind, title, description in legend:
        swatch_x = box_x + 28
        swatch_y = row_y - 7
        if kind == "soportal":
            draw_hatched_swatch(pdf, swatch_x, swatch_y, 26, 26)
        else:
            colour = GREEN if kind == "private" else YELLOW
            pdf.setFillColorRGB(*(channel / 255 for channel in colour))
            pdf.roundRect(swatch_x, swatch_y, 26, 26, 5, stroke=0, fill=1)
        pdf.setFillColorRGB(*(channel / 255 for channel in NAVY))
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(box_x + 70, row_y + 8, title)
        pdf.setFillColorRGB(*(channel / 255 for channel in MUTED))
        pdf.setFont("Helvetica", 9.3)
        pdf.drawString(box_x + 70, row_y - 7, description)
        row_y -= 58

    draw_label(pdf, "Bloque 1", 1531, 682, 90)
    draw_label(pdf, "Bloque 2", 1455, 145)
    draw_label(pdf, "Bloque 3", 1058, 122)
    draw_label(pdf, "Bloque 4", 592, 122)
    draw_label(pdf, "Bloque 5", 123, 145)
    draw_label(pdf, "Bloque 6", 79, 682, 90)

    pdf.setStrokeColorRGB(0.82, 0.85, 0.84)
    pdf.setLineWidth(0.7)
    pdf.line(48, 62, PAGE_W - 48, 62)
    pdf.setFillColorRGB(*(channel / 255 for channel in MUTED))
    pdf.setFont("Helvetica", 9.4)
    pdf.drawString(48, 42, "Versión anonimizada: se han eliminado cotas, nombres de locales, viviendas, estancias y símbolos técnicos internos.")
    pdf.drawString(48, 27, "El rayado del soportal es orientativo. Para una delimitación definitiva deben comprobarse el trazado y el voladizo con el plano acotado y un técnico.")
    pdf.setFillColorRGB(*(channel / 255 for channel in NAVY))
    pdf.setFont("Helvetica-Bold", 9.5)
    pdf.drawRightString(PAGE_W - 48, 27, "UNA FIGURA - SEIS BLOQUES")

    pdf.showPage()
    pdf.save()


if __name__ == "__main__":
    extract_and_simplify_plan()
    build_pdf()
    print(OUTPUT.resolve())
