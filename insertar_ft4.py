# -*- coding: utf-8 -*-
"""Inserta la seccion F.T.4 - Implementacion en el documento vigente del Ciclo 1.

El original NO se modifica: se trabaja sobre una copia. El contenido se inserta
justo debajo del titulo "F.T.4 - Implementacion" (que hoy esta vacio), usando los
estilos propios del documento destino para que la seccion no desentone.

Reutiliza los helpers de formato ya escritos en md_to_docx.py (add_inline_runs,
set_cell_shading, parse_table) en vez de reescribirlos.

Uso:
    py -3.13 insertar_ft4.py
"""

import os
import re
import shutil
import sys

from docx import Document
from docx.shared import Pt, Cm, RGBColor

from md_to_docx import add_inline_runs, set_cell_shading, parse_table

BASE = r"G:\sistemas de informacion 2 angelica garzon\fashonstore parcial si2"
SRC_MD = os.path.join(BASE, r"tienda_ropa\docs\ft4_implementacion.md")
SRC_DOCX = os.path.join(BASE, r"documentos presentacion\FashionStore_Presentacion1_Ciclo1 .docx")
OUT_DOCX = os.path.join(BASE, r"documentos presentacion\FashionStore_Presentacion2_Ciclo1.docx")
IMG_DIR = os.path.join(BASE, "imagenes")

IMG_RE = re.compile(r'^\[\[IMAGEN:([^|\]]+)\|(.*)\]\]$')


def find_heading(doc, texto, nivel=None):
    """Devuelve el parrafo de encabezado cuyo texto contiene `texto`."""
    for p in doc.paragraphs:
        if not p.style.name.startswith('Heading'):
            continue
        if nivel is not None and p.style.name != f'Heading {nivel}':
            continue
        if texto.lower() in p.text.lower():
            return p
    return None


class Insertor:
    """Crea elementos al final del documento y los mueve delante del ancla,
    de modo que queden en orden en el lugar correcto.

    python-docx solo sabe agregar al final; mover el XML resultante con
    addprevious() es la via soportada para insertar en medio del cuerpo.
    """

    def __init__(self, doc, ancla):
        self.doc = doc
        self.ancla = ancla._p

    def parrafo(self, estilo=None):
        p = self.doc.add_paragraph(style=estilo) if estilo else self.doc.add_paragraph()
        self.ancla.addprevious(p._p)
        return p

    def encabezado(self, nivel):
        p = self.doc.add_paragraph(style=f'Heading {nivel}')
        self.ancla.addprevious(p._p)
        return p

    def tabla(self, filas):
        if not filas:
            return
        ncols = max(len(f) for f in filas)
        tabla = self.doc.add_table(rows=0, cols=ncols)
        try:
            tabla.style = 'Table Grid'   # el estilo que ya usan las 21 tablas del documento
        except KeyError:
            pass
        for ridx, fila in enumerate(filas):
            celdas = tabla.add_row().cells
            for cidx in range(ncols):
                texto = fila[cidx] if cidx < len(fila) else ''
                para = celdas[cidx].paragraphs[0]
                add_inline_runs(para, texto)
                for run in para.runs:
                    run.font.size = Pt(9)
                if ridx == 0:
                    for run in para.runs:
                        run.bold = True
                        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                    set_cell_shading(celdas[cidx], '1F2937')
        self.ancla.addprevious(tabla._tbl)
        self.parrafo()

    def imagen(self, ruta, epigrafe):
        p = self.parrafo()
        p.alignment = 1  # centrado
        p.add_run().add_picture(ruta, width=Cm(16))
        cap = self.parrafo()
        cap.alignment = 1
        run = cap.add_run(epigrafe)
        run.italic = True
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x6B, 0x6B, 0x6B)


def main():
    if not os.path.exists(SRC_DOCX):
        sys.exit(f'ERROR: no se encontro el documento original:\n  {SRC_DOCX}')

    shutil.copy2(SRC_DOCX, OUT_DOCX)
    doc = Document(OUT_DOCX)

    ancla = find_heading(doc, 'Bibliograf', nivel=1)
    if ancla is None:
        sys.exit('ERROR: no se encontro el encabezado "Bibliografia" que sirve de ancla.')

    if find_heading(doc, 'Implementaci', nivel=1) is None:
        sys.exit('ERROR: no se encontro el titulo "F.T.4 - Implementacion" en el documento.')

    ins = Insertor(doc, ancla)

    with open(SRC_MD, encoding='utf-8') as f:
        lineas = f.read().split('\n')

    faltantes = []
    i, n = 0, len(lineas)
    while i < n:
        stripped = lineas[i].strip()

        if stripped == '':
            i += 1
            continue

        if stripped.startswith('|'):
            filas, i = parse_table(lineas, i)
            ins.tabla(filas)
            continue

        m = IMG_RE.match(stripped)
        if m:
            ruta = os.path.join(IMG_DIR, m.group(1))
            if os.path.exists(ruta):
                ins.imagen(ruta, m.group(2))
            else:
                faltantes.append(m.group(1))
                p = ins.parrafo()
                run = p.add_run(f'[PENDIENTE: exportar {m.group(1)} desde Enterprise Architect]')
                run.italic = True
                run.font.color.rgb = RGBColor(0xDC, 0x26, 0x26)
            i += 1
            continue

        m = re.match(r'^(#{1,5})\s+(.*)$', stripped)
        if m:
            nivel = min(len(m.group(1)), 4)
            add_inline_runs(ins.encabezado(nivel), m.group(2))
            i += 1
            continue

        m = re.match(r'^[-*]\s+(.*)$', stripped)
        if m:
            add_inline_runs(ins.parrafo('List Bullet'), m.group(1))
            i += 1
            continue

        m = re.match(r'^(\d+)\.\s+(.*)$', stripped)
        if m:
            add_inline_runs(ins.parrafo('List Number'), m.group(2))
            i += 1
            continue

        add_inline_runs(ins.parrafo(), stripped)
        i += 1

    doc.save(OUT_DOCX)
    print('OK ->', OUT_DOCX)
    if faltantes:
        print('AVISO: faltan imagenes, quedaron marcadas como PENDIENTE en el documento:')
        for f_ in faltantes:
            print('   -', os.path.join(IMG_DIR, f_))


if __name__ == '__main__':
    main()
