"""Fiume: parte bagnata più sottile con due strisce d'argilla a pelo d'acqua; bordi sotto le sponde; foce."""
import numpy as np, math, collections
from scipy import ndimage
import ops, geo

LOG = []
def log(s): LOG.append(s); print('[fiume]', s)

def water_cells(m, comp):
    o = m.obj('Acqua'); cells = {}
    for fi in comp['faces']:
        P = m.V[np.array(o['faces'][fi]) - 1]
        i = int(round(P[:, 0].min() / 0.9)) - m.I0; j = int(round((P[:, 2].min() - 0.5) / 0.9)) - m.J0
        cells[(i, j)] = (fi, float(P[:, 1].mean()))
    return cells

def run(m):
    o = m.obj('Acqua')
    big = max(m.comps('Acqua'), key=lambda c: len(c['faces']))
    cells = water_cells(m, big)
    NI, NJ = m.M.shape
    Wm = np.zeros((NI, NJ), bool); Lv = np.full((NI, NJ), np.nan)
    for (i, j), (fi, y) in cells.items():
        Wm[i, j] = True; Lv[i, j] = y
    Xc, Zc = m.cell_xz()
    delete = []
    # --- A) foce: la "lastra" d'acqua dolce sopra il mare (complanare a -0.88) viene tolta oltre la linea di costa
    tongue = Wm & (Xc >= 198.5)
    for (i, j) in zip(*np.nonzero(tongue)):
        delete.append(cells[(i, j)][0])
    Wm &= ~tongue
    log('foce: tolte %d celle d\'acqua dolce sovrapposte al mare (lastra rettangolare complanare a -0.88 m)' % int(tongue.sum()))
    # --- B) restringimento con riva continua: la superficie d'acqua resta, il fondo vicino alle sponde sale
    #        a pelo d'acqua (+3..+10 cm) su una fascia di ~1.1 m: la linea di riva segue una distanza smussata
    NIv, NJv = m.H.shape
    # maschera e livello ai vertici della griglia
    Wv = np.zeros((NIv, NJv), bool); Lvv = np.zeros((NIv, NJv)); cnt = np.zeros((NIv, NJv))
    for (i, j) in zip(*np.nonzero(Wm)):
        for di, dj in ((0, 0), (1, 0), (0, 1), (1, 1)):
            Wv[i + di, j + dj] = True; Lvv[i + di, j + dj] += Lv[i, j]; cnt[i + di, j + dj] += 1
    Lvv = np.where(cnt > 0, Lvv / np.maximum(cnt, 1), np.nan)
    # vertici interni (circondati da acqua) vs bordo
    inner = ndimage.binary_erosion(Wv, structure=np.ones((3, 3)))
    din = ndimage.distance_transform_edt(inner) * 0.9           # distanza dalla sponda in metri
    din = ndimage.gaussian_filter(din, 1.0)
    half = ndimage.maximum_filter(din, size=11)                   # mezza larghezza locale
    X, Z = m.grid_xz()
    rngv = (X > -182) & (X < 176)
    S = 1.1                                                        # larghezza della striscia d'argilla
    ok = Wv & rngv & (half > 2.2) & ~np.isnan(Lvv)
    Lf = np.where(np.isnan(Lvv), 0, Lvv)
    strip_h = Lf + 0.03 + 0.07 * np.clip(1 - din / S, 0, 1)      # +10 cm alla sponda, +3 cm verso l'acqua
    w = np.clip((S + 0.5 - din) / 0.5, 0, 1)                       # 1 sulla striscia, raccordo di 0.5 m verso il letto
    newH = np.where(ok, np.maximum(m.H, strip_h * w + m.H * (1 - w)), m.H)
    changed = ok & (newH > m.H + 0.01)
    m.H = newH
    # materiale argilla sulle celle della striscia
    cellstrip = np.zeros(m.M.shape, bool)
    cs_ = changed[:-1, :-1] | changed[1:, :-1] | changed[:-1, 1:] | changed[1:, 1:]
    cellstrip = cs_ & Wm
    m.M[cellstrip] = m.mat_index('terrain_clay')
    # larghezza bagnata prima/dopo: celle con almeno un vertice sott'acqua
    wet_before = []; wet_after = []
    for i in range(m.M.shape[0]):
        row = Wm[i] & ((Xc[i] > -182) & (Xc[i] < 176))
        if row.sum():
            wet_before.append(row.sum() * 0.9)
            Hc = (m.H[i, :-1] + m.H[i + 1, :-1] + m.H[i, 1:] + m.H[i + 1, 1:]) / 4
            wet_after.append((row & (Hc < np.nan_to_num(Lv[i], nan=-99))).sum() * 0.9)
    log('restringimento: fascia d\'argilla di %.1f m per lato a pelo d\'acqua su %d celle; larghezza bagnata media %.1f -> %.1f m' % (S, int(cellstrip.sum()), np.mean(wet_before), np.mean(wet_after)))
    strip = cellstrip
    keep = Wm
    # --- C) foce: imbuto sabbioso fra X 184 e 199 (sponde a scarpata dolce), barra trasversale, fondale basso
    zc = -79.8
    hw = np.clip(4.2 + (X - 184.0) * 0.5, 4.2, 11.8)
    core = hw - 3.2
    dz = np.abs(Z - zc)
    inx = (X > 183) & (X < 199.5)
    flat_h = np.interp(X, [184, 199.5], [-0.35, -0.66])
    target = np.where(dz < core, np.minimum(m.H, -1.3), flat_h)
    wgt = inx * (1 - ops.smoothstep(hw, hw + 4.5, dz))
    wgt *= ops.smoothstep(183, 186, X)
    m.H = np.where(wgt > 0, m.H * (1 - wgt) + np.where(dz < core, target, np.minimum(m.H, flat_h) if False else flat_h) * wgt, m.H)
    Xg, Zg = Xc, Zc
    hwc = np.clip(4.2 + (Xg - 184.0) * 0.5, 4.2, 11.8)
    band = (Xg > 184) & (Xg < 199.5) & (np.abs(Zg - zc) > hwc - 3.2) & (np.abs(Zg - zc) < hwc + 1.0)
    m.M[band & (Xg > 190)] = m.mat_index('sand')
    m.M[band & (Xg <= 190)] = m.mat_index('terrain_clay')
    # barra sabbiosa trasversale (lungo la costa) che chiude in parte la bocca
    d = ((X - 201.2) / 1.6) ** 2 + ((Z + 72.5) / 5.5) ** 2
    w2 = 1 - ops.smoothstep(0.35, 1.0, d)
    m.H = m.H * (1 - w2) + (-0.74) * w2
    dc = ((Xc - 201.2) / 1.6) ** 2 + ((Zc + 72.5) / 5.5) ** 2
    m.M[dc < 0.8] = m.mat_index('sand')
    # cono di foce: fondale più basso davanti alla bocca
    d = ((X - 207) / 10.0) ** 2 + ((Z - zc) / 13.0) ** 2
    w3 = (1 - ops.smoothstep(0.2, 1.0, d)) * (X > 199.5)
    m.H = np.where(m.H < -1.0, m.H * (1 - w3 * 0.6) + (-1.3) * w3 * 0.6, m.H)
    log('foce: imbuto sabbioso largo da 8 a 24 m con sponde a scarpata dolce, barra sabbiosa trasversale, fondale più basso nel cono di foce')
    # --- D) acqua del canale di foce fino alla costa: celle nuove al livello del fiume dove il terreno ora è sotto
    add_P = []; add_F = []
    for i in range(NI):
        for j in range(NJ):
            if not (186 <= Xc[i, j] <= 198.4 and -94 <= Zc[i, j] <= -66): continue
            if keep[i, j]: continue
            continue
            # livello: interpolazione lungo X fra -0.52 (X 188) e -0.84 (X 198)
            y = float(np.interp(Xc[i, j], [186, 198.4], [-0.47, -0.84]))
            corners = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            hmin = min(m.H[a, b] for a, b in corners)
            if hmin < y - 0.08:
                # la cella è sott'acqua: aggiungo la faccia; i vertici di bordo restano sotto le sponde
                b0 = len(add_P)
                xs = [0.9 * (a + m.I0) for a, b in corners]; zs = [0.5 + 0.9 * (b + m.J0) for a, b in corners]
                add_P += [(x, y, z) for x, z in zip(xs, zs)]
                add_F.append([b0, b0 + 3, b0 + 2, b0 + 1])
    # cancellazioni e aggiunte sull'oggetto Acqua
    m.delete({'Acqua': sorted(set(delete))})
    # livello dell'acqua raccordato al mare negli ultimi metri (niente gradino alla bocca)
    m.invalidate('Acqua'); o = m.obj('Acqua')
    big = max(m.comps('Acqua'), key=lambda c: len(c['faces']))
    vv = big['verts']; P = m.V[vv]
    sel = P[:, 0] > 186.0
    m.V[vv[sel], 1] = np.minimum(P[sel, 1], np.interp(P[sel, 0], [186.0, 198.4], [-0.50, -0.86]))
    m.invalidate('Acqua')
    if add_F:
        me = geo.Mesh().add(add_P, add_F, 'water'); geo.orient(me, lambda c, n: n[1] > 0)
        m.add_faces('Acqua', me.P, me.F, me.M, True)
    log('foce: %d celle d\'acqua aggiunte nel canale allargato fino alla costa' % len(add_F))
    # --- E) canneto lungo le strisce d'argilla e alla foce (oggetto nuovo)
    rng_ = np.random.default_rng(11)
    reed = geo.Mesh(); nclump = 0
    cand = [(Xc[i, j], Zc[i, j]) for i, j in zip(*np.nonzero(strip)) if Xc[i, j] > -150]
    cand += [(x, z) for x, z in zip(Xc[(m.M == m.mat_index('terrain_clay')) & (Xc > 184) & (Xc < 196)], Zc[(m.M == m.mat_index('terrain_clay')) & (Xc > 184) & (Xc < 196)])]
    rng_.shuffle(cand)
    for (x, z) in cand[:int(len(cand) * 0.22)]:
        y0 = float(m.height(x, z))
        for k in range(rng_.integers(4, 8)):
            px = x + rng_.uniform(-0.35, 0.35); pz = z + rng_.uniform(-0.35, 0.35)
            h = rng_.uniform(0.9, 1.7); a = rng_.uniform(0, math.pi); lean = rng_.uniform(-0.12, 0.12, 2)
            w = 0.035
            P = [(px - w * math.cos(a), y0 - 0.05, pz - w * math.sin(a)), (px + w * math.cos(a), y0 - 0.05, pz + w * math.sin(a)),
                 (px + lean[0], y0 + h, pz + lean[1])]
            reed.add(P, [[0, 1, 2]], 'reed')
        nclump += 1
    reed.to_model(m, 'Canneto_Fiume', after='Acqua')
    log('canneto: %d ciuffi (%d facce) lungo le strisce d\'argilla e alla foce (oggetto nuovo Canneto_Fiume)' % (nclump, len(reed.F)))
    # --- F) bordi dell'acqua: nessun bordo sospeso sopra il terreno (vertici di bordo sulla griglia)
    o = m.obj('Acqua'); m.invalidate('Acqua')
    raised = 0
    for c in m.comps('Acqua'):
        F = [np.array(o['faces'][i]) - 1 for i in c['faces']]
        val = collections.Counter(np.concatenate(F))
        for v, k in val.items():
            if k >= 4: continue
            p = m.V[v]
            gi = p[0] / 0.9 - m.I0; gj = (p[2] - 0.5) / 0.9 - m.J0
            if abs(gi - round(gi)) > 0.01 or abs(gj - round(gj)) > 0.01: continue
            gi, gj = int(round(gi)), int(round(gj))
            if 0 <= gi < NI + 1 and 0 <= gj < NJ + 1 and m.H[gi, gj] < p[1] + 0.02:
                m.H[gi, gj] = p[1] + 0.03; raised += 1
    log('bordi dell\'acqua portati sotto le sponde: %d vertici di terreno rialzati di pochi cm' % raised)
    return LOG
