"""Fase 3 - strade e sentieri.
1) Strada del paese dell'altopiano verso il fiume: sulla riva sinistra c'è un ripiano piano a ~1,9 m, scavato ai piedi del
   gradino di roccia (il solco). Il tratto di fondovalle cucito in fase 1 passava invece nell'argilla della riva e in due
   punti dentro l'acqua. La strada viene spostata nel solco, dalla strada del ponte fino all'inizio della rampa nel
   solco che sale verso i tornanti; le celle del vecchio tracciato tornano argilla o prato.
2) Sentieri sottili fra boschi e montagne: percorso di costo minimo sulla griglia (pendenza lungo il passo, tornanti
   naturali dove il versante è ripido), largo circa 1 m, appena inciso nel terreno."""
import numpy as np, math, collections
from scipy import ndimage
import scipy.sparse as sp
from scipy.sparse.csgraph import dijkstra
import ops
from borgo import liscia_linea, resample, limita_pendenza
from alberi_util import gruppi_alberi
from occupancy import occupancy_fine

LOG = []
def log(s): LOG.append(s); print('[strade]', s)

ALBERI = ('Alberi', 'Alberi_Nuovi', 'Alberi_Aree_Nuove', 'Alberi_Infittimento')

def togli_lungo(m, P, r_alberi=1.2, r_sassi=0.8, nomi=ALBERI + ('Rocce', 'Rocce_Promontori', 'Siepi_e_Confini', 'Animali')):
    """alberi (interi) e sassi il cui piede cade a meno di r dalla linea"""
    from shapely.geometry import LineString, Point
    L = LineString(P); bb = L.bounds
    rem = {}; n = collections.Counter()
    for nm in nomi:
        if not m.has(nm): continue
        cs = [c for c in m.comps(nm) if c['hi'][0] >= bb[0] - 3 and c['lo'][0] <= bb[2] + 3 and c['hi'][2] >= bb[1] - 3 and c['lo'][2] <= bb[3] + 3]
        if not cs: continue
        gr = gruppi_alberi(m, nm, cs) if nm in ALBERI else [[c] for c in cs]
        fs = []
        for g in gr:
            b = min(g, key=lambda c: c['lo'][1]); ce = (b['lo'] + b['hi']) / 2
            r = r_alberi if nm in ALBERI else r_sassi + 0.5 * max(b['hi'][0] - b['lo'][0], b['hi'][2] - b['lo'][2])
            if L.distance(Point(ce[0], ce[2])) < r:
                for c in g: fs += c['faces']
                n[nm] += 1
        if fs: rem[nm] = fs
    m.delete(rem)
    return n

# ---------------------------------------------------------------- 1) solco lungo il fiume
SOLCO_PUNTI = [(-27.0, -96.5), (-20.0, -98.6), (-13.0, -102.6), (-6.0, -106.0), (0.0, -108.0), (6.0, -109.8), (12.0, -110.6),
               (18.0, -110.6), (24.0, -109.6), (30.0, -107.4), (36.0, -104.8), (42.0, -102.6), (48.0, -100.4), (53.0, -98.6), (58.0, -97.6)]

def solco(m):
    nomi = lambda: np.array(m.mats + ['<buco>'])[m.M]
    Xc, Zc = m.cell_xz()
    # vecchio tracciato di fondovalle (fase 1) fra x -16 e 47: celle di strada vicino all'acqua
    vecchio = (nomi() == 'path_dirt') & (Xc > -16) & (Xc < 47) & (Zc > -106) & (Zc < -93)
    Pp, s = resample(liscia_linea(SOLCO_PUNTI, 2), 0.5)
    h0 = m.height(Pp[:, 0], Pp[:, 1])
    # quote: capi agganciati alla strada esistente, in mezzo il ripiano del solco (>= 1,8 m: sopra l'argilla bagnata)
    t = ndimage.uniform_filter1d(np.maximum(h0, 1.85), 11, mode='nearest')
    fissi = np.zeros(len(t), bool); fissi[:3] = True; fissi[-3:] = True
    t[:3] = h0[:3]; t[-3:] = h0[-3:]
    h = limita_pendenza(t, s, 0.08, fissi)
    ops.carve_path(m, [tuple(p) for p in Pp], list(h), width=3.0, shoulder=1.6, mat='path_dirt')
    # celle del vecchio tracciato non riusate: argilla se vicino all'acqua, altrimenti come i vicini
    d, _, _ = ops.dist_to_polyline(Xc, Zc, Pp)
    vecchio &= d > 2.0
    bassa = m.H[:-1, :-1] < 1.2
    m.M[vecchio & bassa] = m.mat_index('terrain_clay')
    ops.fill_mat_from_neighbors(m, vecchio & ~bassa, exclude=('path_dirt',))
    g = np.abs(np.diff(h)) / np.diff(s)
    n = togli_lungo(m, Pp, 1.8, 1.0)
    log('strada del fiume spostata nel solco della riva sinistra: %.0f m, quota %.1f-%.1f m (il vecchio tratto stava a %.1f-%.1f m, dentro l\'argilla e in 2 punti nell\'acqua), pendenza max %.1f%%; %d celle del vecchio tracciato tornate argilla o prato; tolti %s'
        % (s[-1], h.min(), h.max(), -0.9, 0.9, g.max() * 100, int(vecchio.sum()), dict(n)))
    return Pp, h

# ---------------------------------------------------------------- 2) sentieri
def griglia_costi(m, x0, x1, z0, z1, passo=1.8, vietati=None):
    xs = np.arange(x0, x1, passo); zs = np.arange(z0, z1, passo)
    X, Z = np.meshgrid(xs, zs, indexing='ij')
    H = m.height(X.ravel(), Z.ravel()).reshape(X.shape)
    H = ndimage.gaussian_filter(H, 1.2)          # pendenza del versante, non delle faccette di roccia
    blocco = np.zeros(X.shape, bool)
    if vietati is not None:
        fi, fj = m.ij(X, Z)
        fi = np.clip(np.floor(fi).astype(int), 0, vietati.shape[0] - 1); fj = np.clip(np.floor(fj).astype(int), 0, vietati.shape[1] - 1)
        blocco = vietati[fi, fj]
    return X, Z, H, blocco

def percorso(m, a, b, box, vietati, gmax=0.30, gbuona=0.16, passo=1.8):
    X, Z, H, blocco = griglia_costi(m, *box, passo=passo, vietati=vietati)
    for p in (a, b):                                    # partenza e arrivo: sgombri (lastre di strada, minuterie)
        blocco &= (X - p[0]) ** 2 + (Z - p[1]) ** 2 > 25.0
    NI, NJ = X.shape
    idx = np.arange(NI * NJ).reshape(NI, NJ)
    mosse = [(1, 0), (0, 1), (1, 1), (1, -1), (2, 1), (1, 2), (2, -1), (1, -2)]
    rows = []; cols = []; w = []
    for di, dj in mosse:
        i0 = slice(max(0, -di), NI - max(0, di)); i1 = slice(max(0, -di) + di, NI - max(0, di) + di)
        j0 = slice(max(0, -dj), NJ - max(0, dj)); j1 = slice(max(0, -dj) + dj, NJ - max(0, dj) + dj)
        a_ = idx[i0, j0]; b_ = idx[i1, j1]
        L = passo * math.hypot(di, dj)
        g = np.abs(H[i1, j1] - H[i0, j0]) / L
        c = L * (1 + 25 * np.maximum(g - gbuona, 0) ** 2 * 10)
        ok = (g <= gmax) & ~blocco[i0, j0] & ~blocco[i1, j1]
        rows += [a_[ok].ravel(), b_[ok].ravel()]; cols += [b_[ok].ravel(), a_[ok].ravel()]; w += [c[ok].ravel(), c[ok].ravel()]
    G = sp.csr_matrix((np.concatenate(w), (np.concatenate(rows), np.concatenate(cols))), shape=(NI * NJ, NI * NJ))
    def nodo(p):
        d = (X - p[0]) ** 2 + (Z - p[1]) ** 2
        d[blocco] = np.inf
        return int(np.argmin(d))
    sa, sb = nodo(a), nodo(b)
    dist, pred = dijkstra(G, indices=sa, return_predecessors=True)
    if not np.isfinite(dist[sb]):
        # meta irraggiungibile con questa pendenza: il punto raggiungibile più vicino, se è entro 12 m
        dd = np.hypot(X.ravel() - b[0], Z.ravel() - b[1]); dd[~np.isfinite(dist)] = np.inf
        k = int(np.argmin(dd))
        if dd[k] > 12.0: return None
        sb = k
    path = [sb]
    while path[-1] != sa: path.append(pred[path[-1]])
    path = path[::-1]
    P = np.array([(X.ravel()[k], Z.ravel()[k]) for k in path])
    return P

def sentiero(m, nome, a, b, box, vietati, larg=1.1):
    P = None
    for gmax in (0.30, 0.38, 0.48, 0.60):
        P = percorso(m, a, b, box, vietati, gmax=gmax)
        if P is not None: break
    if P is None:
        log('sentiero %s: nessun percorso possibile' % nome); return None
    P = liscia_linea(P, 3)
    Pp, s = resample(P, 0.5)
    t = ndimage.uniform_filter1d(m.height(Pp[:, 0], Pp[:, 1]), 5, mode='nearest')
    # profilo del sentiero: niente gradini oltre il 32% (dove il versante fa un salto il sentiero è inciso o riportato)
    fissi = np.zeros(len(t), bool); fissi[0] = fissi[-1] = True
    h = limita_pendenza(t, s, 0.32, fissi)
    if abs(h[-1] - h[-2]) / (s[-1] - s[-2]) > 0.33 or abs(h[1] - h[0]) / (s[1] - s[0]) > 0.33:
        h = limita_pendenza(t, s, 0.32)
    taglio = float(np.max(t - h)); riporto = float(np.max(h - t))
    if taglio > 2.0:                                     # salto di roccia: gradini fino al 42% piuttosto che una trincea
        h = limita_pendenza(t, s, 0.42, fissi)
        taglio = float(np.max(t - h)); riporto = float(np.max(h - t))
    ops.carve_path(m, [tuple(p) for p in Pp], list(h), width=larg, shoulder=0.9, mat='path_dirt', mat_width=0.95)
    n = togli_lungo(m, Pp, 1.3, 0.7)
    g = np.abs(np.diff(h)) / np.diff(s)
    gg = ndimage.uniform_filter1d(g, 8)
    log('sentiero %s: %.0f m, da quota %.0f a %.0f m (dislivello %.0f m), pendenza media %.0f%%, massima %.0f%% (tratti di 4 m), inciso nel pendio fino a %.1f m e riportato fino a %.1f m nei salti; tolti lungo il sentiero %s'
        % (nome, s[-1], h[0], h[-1], h.max() - h.min(), abs(h[-1] - h[0]) / s[-1] * 100, gg.max() * 100, taglio, riporto, ', '.join('%s %d' % kv for kv in n.items()) or 'niente'))
    return Pp

def run(m):
    solco(m)
    # ostacoli per i sentieri: edifici e manufatti, acqua, campi
    escl = ALBERI + ('Rocce', 'Rocce_Promontori', 'Siepi_e_Confini', 'Animali', 'Canneto_Fiume', 'Pareti_Rocciose', 'Fondale_Esteso', 'Mare')
    occ = occupancy_fine(m, extra_exclude=escl, with_mats=False)
    nomi = np.array(m.mats + ['<buco>'])[m.M]
    occ |= np.isin(nomi, ['<buco>', 'terrain_field', 'crop_green', 'crop_gold', 'sand'])
    occ |= m.H[:-1, :-1] < 0.5
    occ = ndimage.binary_dilation(occ, iterations=1)
    S = {}
    S['pascoli'] = sentiero(m, 'dei pascoli (dal paese dell\'altopiano al bosco e ai prati alti)', (130.0, -266.0), (52.0, -316.0), (20, 160, -342, -240), occ)
    return LOG
