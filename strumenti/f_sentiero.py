"""Sentiero dal ponte sul fiume al paese sull'altopiano: fondovalle continuo + salita a tornanti (<= 15%)."""
import numpy as np, math
from scipy import ndimage
import ops
from f_porte import move_trees_off

LOG = []
def log(s): LOG.append(s); print('[sentiero]', s)

def z_at(m, x, h, zlo=-141.0, zhi=-96.0):
    """quota h sul versante alla coordinata x: z dove il terreno (decrescente con z) vale h"""
    zs = np.arange(zlo, zhi, 0.25); t = m.height(np.full(len(zs), x), zs)
    t = ndimage.uniform_filter1d(t, 9)
    k = np.where((t[:-1] >= h) & (t[1:] < h))[0]
    if len(k) == 0: return float(zs[np.argmin(np.abs(t - h))])
    k = k[0]; f = (t[k] - h) / (t[k] - t[k + 1] + 1e-9)
    return float(zs[k] + 0.25 * f)

def leg(m, x0, x1, h0, h1, step=2.0):
    xs = np.arange(x0, x1, step if x1 > x0 else -step); xs = np.r_[xs, x1]
    hs = np.linspace(h0, h1, len(xs))
    zs = np.array([z_at(m, x, h) for x, h in zip(xs, hs)])
    zs = ndimage.uniform_filter1d(zs, 5, mode='nearest')
    return [(x, z, h) for x, z, h in zip(xs, zs, hs)]

def grade(pts):
    P = np.array(pts); d = np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1]))
    return np.abs(np.diff(P[:, 2])) / np.maximum(d, 1e-6), d.sum()

def run(m):
    Xc, Zc = m.cell_xz()
    names = lambda: np.array(m.mats + ['<buco>'])[m.M]
    # --- 1) fondovalle mancante sulla riva sinistra, fra il tratto che viene dal ponte e quello sotto il versante
    base = [(-24.0, -92.5), (-12.0, -97.5), (4.0, -100.0), (20.0, -100.8), (36.0, -100.0), (48.0, -98.5), (57.0, -97.5)]
    P, t = __import__('f_porte').resample(base, 1.0)
    h = ndimage.uniform_filter1d(m.height(P[:, 0], P[:, 1]), 7, mode='nearest')
    # pendenza massima 10% sul fondovalle
    for i in range(1, len(h)):
        h[i] = np.clip(h[i], h[i - 1] - 0.1, h[i - 1] + 0.1)
    ops.carve_path(m, [tuple(p) for p in P], list(h), width=2.6, shoulder=2.0)
    g1, L1 = grade([(p[0], p[1], hh) for p, hh in zip(P, h)])
    log('fondovalle sulla riva sinistra ricucito: %.0f m (pendenza max %.1f%%)' % (L1, g1.max() * 100))
    # --- 2) salita a tornanti dal fondovalle (X~100, Z~-102) alla via del paese (X 140.5, Z -140)
    h_top = float(m.height(140.5, -140.5)); h_bot = float(m.height(100.0, -102.0))
    # rampe separate di quota ai tornanti (la U del tornante scende di 2 m su ~15 m)
    H1, H2, H3 = 26.8, 19.6, 12.8
    L1 = leg(m, 138.0, 62.0, h_top - 0.3, H1 + 1.0)
    L2 = leg(m, 62.0, 118.0, H1 - 1.0, H2 + 1.0)
    L3 = leg(m, 118.0, 68.0, H2 - 1.0, H3 + 1.0)
    L4 = leg(m, 68.0, 100.0, H3 - 1.0, h_bot + 0.3)
    def hairpin(a, b, out):
        (xa, za, ha), (xb, zb, hb) = a, b
        zm = (za + zb) / 2; sg = np.sign(zb - za)
        return [(xa + out * 0.5, za - 0.8 * sg, None), (xa + out * 0.9, za + (zm - za) * 0.4, None), (xa + out, zm, None),
                (xb + out * 0.9, zb + (zm - zb) * 0.4, None), (xb + out * 0.5, zb + 0.8 * sg, None)]
    route = [(140.5, -141.5, h_top)] + L1 + hairpin(L1[-1], L2[0], -6.0) + L2 + hairpin(L2[-1], L3[0], 6.0) + L3 + hairpin(L3[-1], L4[0], -6.0) + L4 + [(101.5, -101.5, h_bot)]
    # quote mancanti (tornanti) interpolate sulla lunghezza del percorso: pendenza uniforme nel tornante
    xy = np.array([(p[0], p[1]) for p in route]); s = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
    hv = np.array([np.nan if p[2] is None else p[2] for p in route])
    ok = ~np.isnan(hv); hv[~ok] = np.interp(s[~ok], s[ok], hv[ok])
    route = [(p[0], p[1], h) for p, h in zip(route, hv)]
    L1 = route[:len(L1) + 1][1:]
    R = np.array(route)
    g, Ltot = grade(route)
    # vecchio tracciato ripido: celle di strada sul versante fuori dal nuovo percorso tornano prato
    d_new, _, _ = ops.dist_to_polyline(Xc, Zc, R[:, :2])
    old = (names() == 'path_dirt') & (Xc > 96) & (Xc < 165) & (Zc > -139) & (Zc < -103) & (d_new > 2.2)
    old |= (names() == 'path_dirt') & (Xc > 124) & (Xc < 160) & (Zc > -122) & (Zc < -95) & (d_new > 2.2)
    n_old = int(old.sum())
    ops.fill_mat_from_neighbors(m, old)
    RR = np.array(route)
    idx = np.r_[0, np.cumsum([len(L1)])]
    # quattro tratti (rampa + tornante), intagliati dall'alto al basso
    n = len(route); cuts = [0]
    for k in range(1, n - 1):
        if (route[k][0] - route[k - 1][0]) * (route[k + 1][0] - route[k][0]) < 0: cuts.append(k)
    cuts.append(n - 1)
    for a_, b_ in zip(cuts[:-1], cuts[1:]):
        seg = route[max(0, a_ - 3):min(n, b_ + 4)]
        ops.carve_path(m, [tuple(p[:2]) for p in seg], [p[2] for p in seg], width=2.6, shoulder=2.2)
    # passata finale sul solo piano del sentiero: quote di progetto esatte lungo l'asse
    ops.carve_path(m, [tuple(p[:2]) for p in route], [p[2] for p in route], width=2.2, shoulder=0.7)
    # verifica sul terreno finale
    Pf, tf = __import__('f_porte').resample(R[:, :2], 1.0)
    hf = m.height(Pf[:, 0], Pf[:, 1])
    gf = np.abs(np.diff(hf)) / 1.0
    log('salita a tornanti: %.0f m, 4 rampe e 3 tornanti, dislivello %.1f m; pendenza di progetto max %.1f%%, misurata sul terreno p95 %.1f%% max %.1f%%' % (Ltot, h_top - h_bot, g.max() * 100, np.percentile(gf, 95) * 100, gf.max() * 100))
    log('vecchio tracciato ripido (pendenze fino al 275%%): %d celle riportate a prato' % n_old)
    t1 = move_trees_off(m, R[:, :2], 1.8) + move_trees_off(m, P, 1.8)
    log('alberi/rocce spostati fuori dal sentiero: %d' % t1)
    import json
    json.dump(dict(fondovalle=[[float(a), float(b)] for a, b in P], tornanti=[[float(a), float(b), float(c)] for a, b, c in route]),
              open('sentiero_nuovo.json', 'w'))
    return LOG
