"""Operazioni comuni: riappoggio al suolo, sentieri, piazzole, selezioni per area."""
import numpy as np, collections
from scipy import ndimage

def footprint_min(m, lo, hi, n=5):
    xs = np.linspace(lo[0], hi[0], n); zs = np.linspace(lo[2], hi[2], n)
    X, Z = np.meshgrid(xs, zs)
    return float(m.height(X.ravel(), Z.ravel()).min())

def reseat_comp(m, name, comp, sink=0.0):
    """appoggia la componente alla quota più bassa del terreno sotto la sua impronta"""
    target = footprint_min(m, comp['lo'], comp['hi']) - sink
    dy = target - comp['lo'][1]
    m.V[comp['verts'], 1] += dy
    return dy

def in_rect(c, x0, x1, z0, z1):
    ce = (c['lo'] + c['hi']) / 2
    return x0 <= ce[0] <= x1 and z0 <= ce[2] <= z1

def cells_in_poly(m, poly):
    """maschera delle celle il cui centro è dentro il poligono (lista di (x,z))"""
    from matplotlib.path import Path
    X, Z = m.cell_xz()
    return Path(np.array(poly)).contains_points(np.stack([X.ravel(), Z.ravel()], 1)).reshape(X.shape)

def verts_in_poly(m, poly):
    from matplotlib.path import Path
    X, Z = m.grid_xz()
    return Path(np.array(poly)).contains_points(np.stack([X.ravel(), Z.ravel()], 1)).reshape(X.shape)

def dist_to_polyline(X, Z, pts):
    """distanza (e parametro lungo la linea, e indice segmento) di ogni punto dalla polilinea"""
    P = np.asarray(pts, float)
    best = np.full(X.shape, np.inf); tpar = np.zeros(X.shape); seg = np.zeros(X.shape, int)
    L = np.r_[0, np.cumsum(np.hypot(*(P[1:] - P[:-1]).T))]
    for k in range(len(P) - 1):
        a, b = P[k], P[k + 1]; d = b - a; l2 = (d ** 2).sum()
        t = np.clip(((X - a[0]) * d[0] + (Z - a[1]) * d[1]) / l2, 0, 1)
        dist = np.hypot(X - (a[0] + t * d[0]), Z - (a[1] + t * d[1]))
        upd = dist < best
        best[upd] = dist[upd]; tpar[upd] = (L[k] + t * np.sqrt(l2))[upd]; seg[upd] = k
    return best, tpar, L

def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)

def carve_path(m, pts, heights, width=3.0, shoulder=3.0, mat='path_dirt', mat_width=None, keep_mats=()):
    """scava/riempie il terreno lungo la polilinea pts (x,z) con quote heights (per vertice della polilinea,
    interpolate lungo la lunghezza). Piano trasversale orizzontale per width, raccordo morbido su shoulder."""
    X, Z = m.grid_xz()
    d, t, L = dist_to_polyline(X, Z, pts)
    hy = np.interp(t, L, heights)
    w = 1 - smoothstep(width / 2, width / 2 + shoulder, d)
    m.H = m.H * (1 - w) + hy * w
    # materiale
    Xc, Zc = m.cell_xz()
    dc, _, _ = dist_to_polyline(Xc, Zc, pts)
    mw = (mat_width or width) / 2
    sel = dc <= mw
    if keep_mats:
        cur = np.array(m.mats + ['<buco>'])[m.M]
        sel &= ~np.isin(cur, keep_mats)
    sel &= m.M >= 0
    m.M[sel] = m.mat_index(mat)
    return sel

def fill_mat_from_neighbors(m, mask, exclude=('path_dirt',)):
    """assegna alle celle mask il materiale più frequente fra le celle vicine non in mask e non escluse"""
    names = np.array(m.mats + ['<buco>'])
    M = m.M.copy()
    ok = ~mask & ~np.isin(names[M], list(exclude)) & (M >= 0)
    idx = ndimage.distance_transform_edt(~ok, return_distances=False, return_indices=True)
    M2 = M[idx[0], idx[1]]
    m.M[mask & (m.M >= 0)] = M2[mask & (m.M >= 0)]

def flatten_pad(m, poly, y, blend=3.0):
    """piazzola piana a quota y dentro il poligono, raccordata su 'blend' metri"""
    from matplotlib.path import Path
    X, Z = m.grid_xz()
    inside = Path(np.array(poly)).contains_points(np.stack([X.ravel(), Z.ravel()], 1)).reshape(X.shape)
    dist = ndimage.distance_transform_edt(~inside) * 0.9
    w = 1 - smoothstep(0, blend, dist)
    m.H = m.H * (1 - w) + y * w
    return inside

GROUND_OBJS = ('Alberi', 'Alberi_Nuovi', 'Rocce', 'Siepi_e_Confini', 'Animali', 'Canneto_Fiume', 'Salice',
               'Pietre_Miliari', 'Rocce_Promontori')

def follow_terrain(m, H0, names=GROUND_OBJS, maxd=3.0):
    """sposta in verticale gli elementi a terra della variazione di quota del terreno sotto il loro centro"""
    dH = m.H - H0
    if not np.any(np.abs(dH) > 1e-3): return 0
    n = 0
    for nm in names:
        if not m.has(nm): continue
        for c in m.comps(nm):
            ce = (c['lo'] + c['hi']) / 2
            fi, fj = m.ij(ce[0], ce[2])
            i = int(np.clip(np.floor(fi), 0, dH.shape[0] - 2)); j = int(np.clip(np.floor(fj), 0, dH.shape[1] - 2))
            a = np.clip(fi - i, 0, 1); b = np.clip(fj - j, 0, 1)
            d = dH[i, j] * (1 - a) * (1 - b) + dH[i + 1, j] * a * (1 - b) + dH[i, j + 1] * (1 - a) * b + dH[i + 1, j + 1] * a * b
            if abs(d) > 1e-3 and abs(d) < maxd * 4:
                m.V[c['verts'], 1] += d; n += 1
        m.invalidate(nm)
    return n
