"""Mappa di lavoro di una zona: rilievo, curve di livello ogni 1 m (spesse ogni 5), materiali principali, impronte degli oggetti.
Uso: mappa_zona(m, x0, x1, z0, z1, path, px=4, oggetti=[...])"""
import numpy as np
from PIL import Image, ImageDraw

PAL = {'path_dirt': (200, 150, 60), 'street_stone': (220, 60, 60), 'piazza_stone': (240, 120, 180), 'terrain_clay': (150, 110, 80),
       'terrain_rock': (130, 130, 130), 'stone_dark': (95, 95, 95), 'sand': (230, 210, 150), 'terrain_field': (200, 200, 90),
       'crop_green': (150, 200, 80), 'crop_gold': (230, 200, 90), 'terrain_forest': (50, 100, 45), 'terrain_grass': (100, 150, 60),
       'terrain_meadow': (125, 160, 75), 'moss_stone': (110, 120, 90), 'terrain_gravel': (160, 155, 145), 'soil_dark': (90, 70, 50)}

def mappa_zona(m, x0, x1, z0, z1, path, px=4, oggetti=(), segni=(), testo=True):
    i0 = int(np.floor(x0 / 0.9 - m.I0)); i1 = int(np.ceil(x1 / 0.9 - m.I0))
    j0 = int(np.floor((z0 - 0.5) / 0.9 - m.J0)); j1 = int(np.ceil((z1 - 0.5) / 0.9 - m.J0))
    H = m.H[i0:i1 + 1, j0:j1 + 1]
    N = np.array(m.mats + ['<buco>'])[m.M[i0:i1, j0:j1]]
    col = np.zeros(N.shape + (3,))
    for k, v in PAL.items(): col[N == k] = v
    gy, gx = np.gradient(H[:-1, :-1], 0.9)
    sh = np.clip(0.75 + 0.35 * (-gx * 0.5 - gy * 0.5) / np.sqrt(1 + gx ** 2 + gy ** 2), 0.3, 1.2)
    col = col * sh[..., None]
    Hc = (H[:-1, :-1] + H[1:, 1:]) / 2
    c1 = (np.floor(Hc) != np.floor(np.roll(Hc, 1, 0))) | (np.floor(Hc) != np.floor(np.roll(Hc, 1, 1)))
    c5 = (np.floor(Hc / 5) != np.floor(np.roll(Hc / 5, 1, 0))) | (np.floor(Hc / 5) != np.floor(np.roll(Hc / 5, 1, 1)))
    col[c1] *= 0.8; col[c5] *= 0.45
    img = np.clip(col, 0, 255).astype(np.uint8)[::-1]          # alto = +X
    im = Image.fromarray(img).resize((img.shape[1] * px, img.shape[0] * px), Image.NEAREST)
    d = ImageDraw.Draw(im)
    def P(x, z):
        return (((z - 0.5) / 0.9 - m.J0 - j0) * px, (i1 - (x / 0.9 - m.I0)) * px)
    for nm, colr in oggetti:
        if not m.has(nm): continue
        for c in m.comps(nm):
            if c['hi'][0] < x0 or c['lo'][0] > x1 or c['hi'][2] < z0 or c['lo'][2] > z1: continue
            a = P(c['hi'][0], c['lo'][2]); b = P(c['lo'][0], c['hi'][2])
            d.rectangle([a, b], outline=colr)
    for kind, data, colr in segni:
        if kind == 'line': d.line([P(x, z) for x, z in data], fill=colr, width=2)
        elif kind == 'pt':
            for x, z in data:
                q = P(x, z); d.ellipse([q[0] - 3, q[1] - 3, q[0] + 3, q[1] + 3], outline=colr)
    step = 10 if (x1 - x0) <= 200 else 20
    for x in range(int(np.ceil(x0 / step) * step), int(x1) + 1, step):
        q = P(x, z0); d.line([(0, q[1]), (im.width, q[1])], fill=(255, 255, 255), width=1)
        if testo: d.text((2, q[1] + 1), 'x%d' % x, fill=(255, 255, 255))
    for z in range(int(np.ceil(z0 / step) * step), int(z1) + 1, step):
        q = P(x0, z); d.line([(q[0], 0), (q[0], im.height)], fill=(255, 255, 255), width=1)
        if testo: d.text((q[0] + 2, 2), 'z%d' % z, fill=(255, 255, 255))
    im.save(path)
    return im.size
