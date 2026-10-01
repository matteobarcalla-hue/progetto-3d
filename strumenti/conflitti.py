import sys, numpy as np, json
sys.path.insert(0, 'tools')
from stato import carica
from PIL import Image, ImageDraw
m = carica(sys.argv[1])
AREE = {'rocca': (52, 106, -22, 50), 'podere nuovo': (122, 158, -8, 26)}
OBJS = ('Rocca', 'Chiostro', 'Cimitero', 'Oratorio', 'Poderi', 'Poderi_Dettagli', 'Mura', 'Torri', 'Porte', 'Borgo_Alto', 'Fortezza_Dettagli', 'Giardino_Rocca', 'Dettagli_Rocca', 'Presidio', 'Alberi', 'Alberi_Nuovi', 'Rocce')
R = 0.25
for area, (x0, x1, z0, z1) in AREE.items():
    NI = int((x1 - x0) / R); NJ = int((z1 - z0) / R)
    masks = {}
    for nm in OBJS:
        if not m.has(nm): continue
        o = m.obj(nm)
        im = Image.new('1', (NJ, NI), 0); d = ImageDraw.Draw(im); n = 0
        for c in m.comps(nm):
            lo, hi = c['lo'], c['hi']
            if hi[0] < x0 or lo[0] > x1 or hi[2] < z0 or lo[2] > z1: continue
            if nm not in ('Alberi', 'Alberi_Nuovi', 'Rocce') and (hi[1] - lo[1] < 1.8): continue   # solo volumi (edifici, muri)
            for f in c['faces']:
                P = m.V[np.array(o['faces'][f]) - 1]
                pts = [((p[2] - z0) / R, (p[0] - x0) / R) for p in P]
                d.polygon(pts, fill=1); n += 1
        if n: masks[nm] = ndimage_er = np.array(im, bool)
    from scipy import ndimage
    names = sorted(masks)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            A = ndimage.binary_erosion(masks[a], iterations=2); Bm = ndimage.binary_erosion(masks[b], iterations=2)
            ov = (A & Bm).sum() * R * R
            if ov > 0.5: print(area, a, b, 'sovrapposizione in pianta %.1f m2' % ov)
