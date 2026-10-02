"""Fase 3 - pulizia finale dei borghi, sulle impronte esatte delle case nuove (salvate dal generatore):
- alberi, sassi e siepi con vertici dentro il volume di una casa nuova (impronta del corpo ristretta di 0,25 m, dalla
  soglia al colmo): tolti interi;
- case nuove che inglobano un pezzo di un oggetto esistente (non vegetazione): tolte (si toglie il nuovo, mai l'originale)."""
import numpy as np, collections, pickle
from shapely.geometry import Polygon
from matplotlib.path import Path
from alberi_util import gruppi_alberi

LOG = []
def log(s): LOG.append(s); print('[pulizia]', s)
VEG = ('Alberi', 'Alberi_Nuovi', 'Alberi_Aree_Nuove', 'Alberi_Infittimento', 'Siepi_e_Confini', 'Rocce', 'Rocce_Promontori', 'Animali', 'Canneto_Fiume')
SALTA = ('Terreno', 'Base_Sezione', 'Acqua', 'Mare', 'Fondale_Esteso', 'Borgo_Altopiano', 'Borgo_Porto')

def run(m):
    case = pickle.load(open('fase3/case_borghi.pkl', 'rb'))
    vol = []
    for c in case:
        P = Polygon(c['corpo']).buffer(-0.25, join_style=2)
        if P.is_empty: continue
        b = P.bounds
        T = Polygon(c['tutto']); bt = T.bounds                         # con le gronde: per alberi e sassi
        vol.append(dict(c=c, path=Path(np.array(P.exterior.coords)), lo=np.array([b[0], c['y'] + 0.3, b[1]]), hi=np.array([b[2], c['y'] + c['alt'] - 0.3, b[3]]),
                        path_t=Path(np.array(T.exterior.coords)), lo_t=np.array([bt[0], c['y'] + 0.3, bt[1]]), hi_t=np.array([bt[2], c['y'] + c['alt'] + 0.2, bt[3]])))
    LO = np.array([v['lo'] for v in vol]); HI = np.array([v['hi'] for v in vol])
    LOT = np.array([v['lo_t'] for v in vol]); HIT = np.array([v['hi_t'] for v in vol])
    rem = collections.defaultdict(list); n_alb = collections.Counter(); case_via = set(); motivi = []
    for o in m.objs:
        nm = o['name']
        if nm in SALTA or not o['faces']: continue
        cs = m.comps(nm)
        gruppi = gruppi_alberi(m, nm, cs) if nm.startswith('Alberi') else [[c] for c in cs]
        for g in gruppi:
            lo = np.min([c['lo'] for c in g], 0); hi = np.max([c['hi'] for c in g], 0)
            veg = nm in VEG
            L_, H_ = (LOT, HIT) if veg else (LO, HI)
            ov = np.all(np.minimum(H_, hi) > np.maximum(L_, lo), 1)
            for k in np.nonzero(ov)[0]:
                V = np.concatenate([m.V[c['verts']] for c in g])
                vv = V[(V[:, 1] > L_[k, 1]) & (V[:, 1] < H_[k, 1])]
                pth = vol[k]['path_t'] if veg else vol[k]['path']
                if len(vv) < 2 or pth.contains_points(vv[:, [0, 2]]).sum() < 2: continue
                if nm in VEG:
                    for c in g: rem[nm] += c['faces']
                    n_alb[nm] += 1
                else:
                    case_via.add(k); motivi.append((nm, np.round((lo + hi) / 2, 1).tolist(), vol[k]['c']['obj']))
                break
    # case tolte: i loro componenti (dentro l'impronta 'tutto')
    for k in case_via:
        c = vol[k]['c']; P = Path(np.array(c['tutto']))
        o = m.obj(c['obj'])
        for cc in m.comps(c['obj']):
            ce = (cc['lo'] + cc['hi']) / 2
            if P.contains_point((ce[0], ce[2])) and c['y'] - 1.0 < ce[1] < c['y'] + c['alt'] + 1.0:
                rem[c['obj']] += cc['faces']
    m.delete(dict(rem))
    log('alberi, sassi e siepi dentro il volume di una casa nuova, tolti interi: %s' % (', '.join('%s %d' % kv for kv in n_alb.most_common()) or 'nessuno'))
    log('case nuove tolte perché inglobavano un pezzo di un oggetto esistente: %d %s' % (len(case_via), motivi))
    return LOG
