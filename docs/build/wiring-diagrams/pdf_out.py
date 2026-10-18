"""SVG -> PDF with PyMuPDF (pip install pymupdf). Optional: without it only the SVGs are written."""
import os

PT = 72 / 25.4


def available():
    try:
        import fitz   # noqa: F401
        return True
    except ImportError:
        return False


def svg_to_pdf_doc(path):
    import fitz
    return fitz.open('pdf', fitz.open(path).convert_to_pdf())


def write_single(svg, pdf):
    d = svg_to_pdf_doc(svg)
    d.save(pdf)
    d.close()


def write_multi(svgs, pdf):
    import fitz
    out = fitz.open()
    for s in svgs:
        out.insert_pdf(svg_to_pdf_doc(s))
    out.save(pdf)
    out.close()


def write_tiles(svg, pdf, cuts, scale=0.85, page=(420.0, 297.0)):
    """A3 landscape tiles of one big sheet: each cut (y0, y1 in mm) at `scale`, title kept readable."""
    import fitz
    src = svg_to_pdf_doc(svg)
    w_mm = src[0].rect.width / PT
    out = fitz.open()
    for (y0, y1) in cuts:
        pg = out.new_page(width=page[0] * PT, height=page[1] * PT)
        clip = fitz.Rect(0, y0 * PT, src[0].rect.width, y1 * PT)
        tw, th = clip.width * scale, clip.height * scale
        x = (page[0] * PT - tw) / 2
        pg.show_pdf_page(fitz.Rect(x, 6 * PT, x + tw, 6 * PT + th), src, 0, clip=clip)
    out.save(pdf)
    out.close()
