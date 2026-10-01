"""Linee morfologiche dritte lasciate dalle espansioni precedenti: pieghe lungo i vecchi confini del terreno."""
import numpy as np, math
from scipy import ndimage
import ops
from occupancy import occupancy

LOG = []
def log(s): LOG.append(s); print('[linee]', s)

def noise1d(n, scale, seed):
    r = np.random.default_rng(seed).normal(size=n + 64)
    r = ndimage.gaussian_filter1d(r, scale)
    r = r[32:32 + n]; return r / (np.abs(r).max() + 1e-9)

def crease(m, axis, coord, band, sigma, seed, zone=None):
    """smussa la piega lungo la linea (axis=0: X=coord, linea lungo Z; axis=1: Z=coord, linea lungo X)"""
    H = m.H.copy(); X, Z = m.grid_xz()
    d = (X - coord) if axis == 0 else (Z - coord)
    s_idx = np.arange(H.shape[1] if axis == 0 else H.shape[0])
    nz = noise1d(len(s_idx), 18, seed)
    bw = band * (1.0 + 0.45 * nz)                     # fascia di larghezza variabile lungo la linea
    bw = bw[None, :] if axis == 0 else bw[:, None]
    w = 1 - ops.smoothstep(0.0, 1.0, np.abs(d) / bw)
    Hs = ndimage.gaussian_filter1d(H, sigma / 0.9, axis=axis)
    Hs = ndimage.gaussian_filter1d(Hs, 1.2, axis=1 - axis)
    if zone is not None: w *= zone
    before = curvature(H, axis, coord, m)
    m.H = H + w * (Hs - H)
    after = curvature(m.H, axis, coord, m)
    return before, after, float((w > 0.05).sum()) * 0.81

def curvature(H, axis, coord, m):
    if axis == 0:
        i = int(round(coord / 0.9)) - m.I0
        seg = np.abs(H[i + 1] - 2 * H[i] + H[i - 1])
    else:
        j = int(round((coord - 0.5) / 0.9)) - m.J0
        seg = np.abs(H[:, j + 1] - 2 * H[:, j] + H[:, j - 1])
    return float(np.median(seg)), float(np.percentile(seg, 90))

def dither_materials(m, axis, coord, band, seed):
    """confini dei materiali rettilinei lungo la giuntura: spostati con un rumore a bassa frequenza"""
    Xc, Zc = m.cell_xz()
    d = (Xc - coord) if axis == 0 else (Zc - coord)
    n = Xc.shape[1] if axis == 0 else Xc.shape[0]
    off = noise1d(n, 10, seed) * 3.5
    off = off[None, :] if axis == 0 else off[:, None]
    # campiono il materiale da una posizione spostata perpendicolarmente alla linea (solo nella fascia)
    M = m.M.copy()
    sel = np.abs(d) < band
    di = np.round(off / 0.9).astype(int)
    if axis == 0:
        ii = np.clip(np.arange(M.shape[0])[:, None] + di, 0, M.shape[0] - 1)
        src = M[ii, np.arange(M.shape[1])[None, :]]
    else:
        jj = np.clip(np.arange(M.shape[1])[None, :] + di, 0, M.shape[1] - 1)
        src = M[np.arange(M.shape[0])[:, None], jj]
    names = np.array(m.mats + ['<buco>'])
    natural = ('terrain_grass', 'terrain_meadow', 'terrain_forest', 'terrain_rock', 'moss_stone', 'stone_dark', 'terrain_gravel', 'sand', 'terrain_clay')
    ok = sel & np.isin(names[M], natural) & np.isin(names[src], natural) & (M >= 0) & (src >= 0)
    m.M[ok] = src[ok]
    return int((m.M != M).sum())

def run(m):
    # zone protette: edifici e manufatti (non vegetazione), strade, acqua
    occ = occupancy(m, extra_exclude=('Alberi', 'Alberi_Nuovi', 'Rocce', 'Siepi_e_Confini', 'Animali', 'Canneto_Fiume'))
    names = np.array(m.mats + ['<buco>'])[m.M]
    prot = occ | np.isin(names, ['path_dirt', 'street_stone', 'piazza_stone', 'soil_dark', 'terrain_field', 'crop_green'])
    prot = ndimage.binary_dilation(prot, iterations=2)
    free_v = np.ones(m.H.shape)
    pv = np.zeros(m.H.shape, bool)
    pv[:-1, :-1] |= prot; pv[1:, :-1] |= prot; pv[:-1, 1:] |= prot; pv[1:, 1:] |= prot
    zone = ndimage.gaussian_filter((~pv).astype(float), 1.5)
    seams = [(0, -225.0, 14.0, 6.0, 1, 'X = -225 (bordo basso del terreno originale)'),
             (1, -130.3, 11.0, 5.0, 2, 'Z = -130 (bordo sinistro del terreno originale)'),
             (1, -138.1, 8.0, 4.0, 3, 'Z = -138 (fine del raccordo sinistro)'),
             (1, 168.8, 11.0, 5.0, 4, 'Z = 169 (bordo destro del terreno originale)'),
             (1, 178.7, 8.0, 4.0, 5, 'Z = 179 (fine del raccordo destro)')]
    for axis, coord, band, sigma, seed, name in seams:
        b, a, area = crease(m, axis, coord, band, sigma, seed, zone)
        nm = dither_materials(m, axis, coord, band * 0.9, seed + 10)
        log('%s: curvatura sulla linea mediana %.3f -> %.3f, p90 %.3f -> %.3f; fascia smussata %.0f m²; %d celle di materiale con confine non più rettilineo' % (name, b[0], a[0], b[1], a[1], area, nm))
    return LOG
