#!/usr/bin/env python
"""Crop the OEM plug face views named in oem-plugs.json out of the 1993 TIS EWD pages (st185-celica-repair-manual app)
into oem-faces/*.png. Run by hand when oem-plugs.json crops change (needs PyMuPDF); the atlas generator only reads the PNGs.
  python docs/harness/atlas/extract_faces.py [path to st185-celica-repair-manual]"""
import json
import os
import sys

import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
APP = sys.argv[1] if len(sys.argv) > 1 else r'C:\projects\active\st185-celica-repair-manual'
data = json.load(open(os.path.join(HERE, 'oem-plugs.json'), encoding='utf-8'))
k = 72.0 / 110.0   # crop boxes are pixels of a 110 dpi render
for key, p in data['plugs'].items():
    s = p['src']
    doc = fitz.open(os.path.join(APP, 'electrical', 'circuits', s['doc'] + '.pdf'))
    x0, y0, x1, y1 = [v * k for v in s['crop_px110']]
    pix = doc[s['page'] - 1].get_pixmap(dpi=220, clip=fitz.Rect(x0, y0, x1, y1))
    pix.save(os.path.join(HERE, p['face']))
    print(key, p['face'], pix.width, 'x', pix.height)
