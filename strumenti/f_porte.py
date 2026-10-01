"""Accessi alle porte della fortezza attraverso il fossato: rampe continue con pendenza <= 14%."""
import numpy as np, math
import ops

LOG = []
def log(s): LOG.append(s); print('[porte]', s)

def resample(pts, step=0.9):
    P = np.array(pts, float); L = np.r_[0, np.cumsum(np.hypot(*(P[1:] - P[:-1]).T))]
    t = np.linspace(0, L[-1], max(2, int(L[-1] / step) + 1))
    return np.stack([np.interp(t, L, P[:, 0]), np.interp(t, L, P[:, 1])], 1), t

def smooth_line(pts, n=3):
    P = np.array(pts, float)
    for _ in range(n):
        Q = P.copy(); Q[1:-1] = (P[:-2] + 2 * P[1:-1] + P[2:]) / 4; P = Q
    return P

def profile(m, pts, h0, h_end=None, gmax=0.14):
    """quote lungo la polilinea: discesa costante da h0 (a pendenza gmax o fino a h_end), poi segue il terreno"""
    P, t = resample(pts)
    ter = m.height(P[:, 0], P[:, 1])
    if h_end is not None:
        g = min(gmax, (h0 - h_end) / t[-1])
    else:
        g = gmax
    h = h0 - g * t          # rampa lineare: si scava dove il terreno è più alto, si riempie dove è più basso
    return P, h, g

def move_trees_off(m, pts, half_w):
    """sposta lateralmente fuori dalla carreggiata alberi, rocce e siepi che la occupano"""
    P, t = resample(pts, 0.5)
    moved = 0
    for name in ('Alberi', 'Alberi_Nuovi', 'Rocce', 'Siepi_e_Confini'):
        if not m.has(name): continue
        for c in m.comps(name):
            ce = (c['lo'] + c['hi']) / 2
            d = np.hypot(P[:, 0] - ce[0], P[:, 1] - ce[2]); k = int(np.argmin(d))
            rad = max(c['hi'][0] - c['lo'][0], c['hi'][2] - c['lo'][2]) / 2
            if d[k] < half_w + rad * 0.7:
                # direzione normale alla strada
                k2 = min(k + 1, len(P) - 1); k1 = max(k - 1, 0)
                tang = P[k2] - P[k1]; tang /= np.linalg.norm(tang); nrm = np.array([-tang[1], tang[0]])
                side = np.sign(np.dot([ce[0] - P[k, 0], ce[2] - P[k, 1]], nrm)) or 1.0
                shift = (half_w + rad + 0.6 - d[k] * 1.0) * side
                off = nrm * shift
                vs = c['verts']
                m.V[vs, 0] += off[0]; m.V[vs, 2] += off[1]
                lo = m.V[vs].min(0); hi = m.V[vs].max(0)
                m.V[vs, 1] += ops.footprint_min(m, lo, hi) - lo[1] - 0.05
                moved += 1
        m.invalidate(name)
    return moved

def reseat_slabs(m, x0, x1, z0, z1, name='Strade_Rurali'):
    sel = m.select(lambda lo, hi: x0 <= (lo[0] + hi[0]) / 2 <= x1 and z0 <= (lo[2] + hi[2]) / 2 <= z1, names=(name,))
    vs = m.sel_verts(sel)
    if len(vs):
        m.V[vs, 1] = m.height(m.V[vs, 0], m.V[vs, 2]) + 0.06
        m.invalidate(name)
    return len(vs)

def apply(m, name, pts, h0, h_end, width=3.6, shoulder=5.0, old_cells=None):
    P, h, g = profile(m, pts, h0, h_end)
    before = m.height(P[:, 0], P[:, 1])
    gb = np.abs(np.diff(before)) / np.hypot(*np.diff(P, axis=0).T)
    # piattaforma della strada con scarpate
    X, Z = m.grid_xz()
    d, tt, L = ops.dist_to_polyline(X, Z, P)
    hy = np.interp(tt, L, h)
    w = 1 - ops.smoothstep(width / 2 + 0.4, width / 2 + 0.4 + shoulder, d)
    m.H = m.H * (1 - w) + hy * w
    # materiale: strada battuta
    Xc, Zc = m.cell_xz()
    dc, _, _ = ops.dist_to_polyline(Xc, Zc, P)
    m.M[(dc <= width / 2) & (m.M >= 0)] = m.mat_index('path_dirt')
    after = m.height(P[:, 0], P[:, 1])
    ga = np.abs(np.diff(after)) / np.hypot(*np.diff(P, axis=0).T)
    log('%s: rampa di %.0f m, pendenza max prima %.0f%%, dopo %.1f%% (progetto %.1f%%)' % (name, np.hypot(*np.diff(P, axis=0).T).sum(), gb.max() * 100, ga.max() * 100, g * 100))
    return P

def run(m):
    # --- porta bassa: soglia a (-80.6, 30.6)
    h0 = float(m.height(-80.4, 30.6))
    pts = smooth_line([(-80.6, 30.6), (-88.0, 30.6), (-95.0, 31.2), (-99.0, 36.5), (-102.0, 44.0), (-104.5, 52.0)])
    hb = float(m.height(-104.5, 52.0))
    Pb = apply(m, 'porta bassa', pts, h0, hb, width=3.6, shoulder=5.5)
    # tratto vecchio che scendeva dritto dalla lingua di terra alla strada esterna: torna prato e si raccorda
    Xc, Zc = m.cell_xz()
    dnew, _, _ = ops.dist_to_polyline(Xc, Zc, Pb)
    old = (Xc < -94.5) & (Xc > -100.5) & (Zc > 27) & (Zc < 34) & (dnew > 2.5)
    old &= np.isin(np.array(m.mats + ['<buco>'])[m.M], ['path_dirt'])
    ops.fill_mat_from_neighbors(m, old)
    # raccordo morbido del terreno nel tratto abbandonato
    X, Z = m.grid_xz(); from scipy import ndimage
    reg = (X < -93.5) & (X > -101.5) & (Z > 25) & (Z < 36)
    dv, _, _ = ops.dist_to_polyline(X, Z, Pb)
    reg &= dv > 4.0
    Hs = ndimage.uniform_filter(m.H, 5)
    m.H[reg] = Hs[reg]
    n1 = reseat_slabs(m, -88, -78, 25, 36)
    t1 = move_trees_off(m, Pb, 2.4)
    # --- porta destra: soglia a (-57.9, 60.6)
    h0 = float(m.height(-57.9, 60.6))
    pts = [(-57.9, 60.6), (-57.9, 70.0), (-57.6, 80.0), (-57.3, 88.0), (-57.0, 96.0)]
    # punto d'arrivo: dove la rampa al 14% incontra il terreno
    P, t = resample(pts)
    ter = m.height(P[:, 0], P[:, 1]); ramp = h0 - 0.14 * t
    ok = (ramp <= ter + 0.02) & (t > 15.0)
    k = int(np.argmax(ok)) if np.any(ok) else len(P) - 1
    he = float(ter[k])
    Pd = apply(m, 'porta destra', [tuple(p) for p in P[:k + 1]], h0, he, width=3.6, shoulder=5.5)
    n2 = reseat_slabs(m, -62, -54, 59, 68)
    t2 = move_trees_off(m, Pd, 2.4)
    log('lastricati davanti alle porte riappoggiati (%d vertici); alberi/rocce spostati fuori dalla carreggiata: %d' % (n1 + n2, t1 + t2))
    return LOG
