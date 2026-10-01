"""Controlli di realismo/debug aggiuntivi confrontando originale e finale (strade, acqua, alberi su strade, integrità)."""
import sys, os, json, numpy as np, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scipy import ndimage
from stato import carica

def strade(m):
    names = np.array(m.mats + ['<buco>'])[m.M]
    road = np.isin(names, ['path_dirt', 'street_stone', 'piazza_stone'])
    H = m.H
    # pendenza della cella: massima differenza fra spigoli opposti / passo (direzione peggiore)
    gx = ((H[1:, 1:] + H[1:, :-1]) - (H[:-1, 1:] + H[:-1, :-1])) / 1.8
    gz = ((H[1:, 1:] + H[:-1, 1:]) - (H[1:, :-1] + H[:-1, :-1])) / 1.8
    s = np.hypot(gx, gz)
    # escludo le celle di bordo strada (spalle): solo celle con almeno 6 vicini stradali su 8
    nb = ndimage.convolve(road.astype(int), np.ones((3, 3), int), mode='constant') - road
    core = road & (nb >= 6)
    v = s[core]
    return dict(celle=int(core.sum()), p50=round(float(np.percentile(v, 50)) * 100, 1), p95=round(float(np.percentile(v, 95)) * 100, 1),
                p99=round(float(np.percentile(v, 99)) * 100, 1), oltre15=round(float((v > 0.15).mean()) * 100, 2), oltre25=round(float((v > 0.25).mean()) * 100, 2))

def acqua(m):
    o = m.obj('Acqua'); F = [np.array(f) - 1 for f in o['faces']]
    cnt = collections.Counter()
    for f in F:
        for a, b in zip(f, np.roll(f, -1)): cnt[(min(a, b), max(a, b))] += 1
    bv = np.unique([v for e, c in cnt.items() if c == 1 for v in e])
    P = m.V[bv]
    # solo il fiume a quote basse (escludo la cascata e i laghetti in quota sopra 3 m)
    t = m.height_tri(P[:, 0], P[:, 2]); d = P[:, 1] - t
    sel = P[:, 1] < 3.0
    d = d[sel]
    return dict(vertici_di_bordo=int(sel.sum()), sopra_01=int((d > 0.1).sum()), max_sopra=round(float(d.max()), 2), mediana=round(float(np.median(d)), 2))

def alberi_su_strade(m):
    names = np.array(m.mats + ['<buco>'])[m.M]
    road = np.isin(names, ['path_dirt', 'street_stone', 'piazza_stone'])
    road = ndimage.binary_erosion(road, iterations=1)
    n = 0; tot = 0
    for nm in ('Alberi', 'Alberi_Nuovi', 'Alberi_Aree_Nuove', 'Alberi_Infittimento'):
        if not m.has(nm): continue
        for c in m.comps(nm):
            if c['hi'][1] - c['lo'][1] < 1.5: continue      # chiome e piccoli pezzi: conto solo i tronchi/alberi interi
            ce = (c['lo'] + c['hi']) / 2; i, j = m.ij(ce[0], ce[2]); i = int(np.floor(i)); j = int(np.floor(j))
            if 0 <= i < road.shape[0] and 0 <= j < road.shape[1]:
                tot += 1; n += int(road[i, j])
    return dict(componenti=tot, su_strada=n)

def run(stato_fin, out):
    m0 = carica(None); m1 = carica(stato_fin)
    R = {}
    R['strade_pendenza_orig'] = strade(m0); R['strade_pendenza_fin'] = strade(m1)
    R['acqua_bordi_orig'] = acqua(m0); R['acqua_bordi_fin'] = acqua(m1)
    R['alberi_su_strade_orig'] = alberi_su_strade(m0); R['alberi_su_strade_fin'] = alberi_su_strade(m1)
    f0 = {o['name']: len(o['faces']) for o in m0.objs}; f1 = {o['name']: len(o['faces']) for o in m1.objs}
    f0['Terreno'] = int((m0.M >= 0).sum()); f1['Terreno'] = int((m1.M >= 0).sum())
    R['oggetti_nuovi'] = sorted(set(f1) - set(f0)); R['oggetti_rimossi'] = sorted(set(f0) - set(f1))
    R['facce_variate'] = {k: [f0.get(k, 0), f1.get(k, 0)] for k in sorted(set(f0) | set(f1)) if f0.get(k, 0) != f1.get(k, 0)}
    R['grotte_celle'] = [int((m0.M < 0).sum()), int((m1.M < 0).sum())]
    json.dump(R, open(out, 'w'), indent=1, ensure_ascii=False)
    print(json.dumps(R, indent=1, ensure_ascii=False))

if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
