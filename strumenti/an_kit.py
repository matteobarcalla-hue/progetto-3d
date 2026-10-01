import sys, json, numpy as np, ast
sys.path.insert(0, 'tools')
from stato import carica
from occupancy import occupancy_fine
from scipy import ndimage
ESCL = ('Alberi', 'Alberi_Nuovi', 'Rocce', 'Rocce_Promontori', 'Pareti_Rocciose', 'Siepi_e_Confini', 'Animali', 'Canneto_Fiume', 'Strade_Rurali', 'Strade_Borgo',
        'Ponte', 'Ponti_Nuovi', 'Ponticelli', 'Porte', 'Dettagli_Porte_Fortezza', 'Salice', 'Pietre_Miliari', 'Fontanelle', 'Arredo_Piazza', 'Mercati', 'Capitelli', 'Capitelli_Nuovi',
        'Dettagli_Borgo_Basso', 'Dettagli_Borgo_Alto', 'Campi', 'Guglie')
d = ast.literal_eval(open('kit.py').read().split('\n')[30].split('=', 1)[1].strip())
def viol(m, tag):
    occ = occupancy_fine(m, extra_exclude=ESCL, with_mats=False)
    Hs = m.H; gx, gz = np.gradient(Hs, 0.9); sl = np.hypot(gx, gz)
    def bad(x, z):
        i, j = m.ij(np.asarray(x), np.asarray(z)); i = np.clip(np.floor(i).astype(int), 0, occ.shape[0]-1); j = np.clip(np.floor(j).astype(int), 0, occ.shape[1]-1)
        return occ[i, j]
    out = {}
    for ri, rt in enumerate(d['percorsi']):
        P = np.array(rt['punti']); b = bad(P[:, 0], P[:, 1]); out[('p', ri)] = set(np.where(b)[0])
    for ai, a in enumerate(d['animali']):
        if a['anello']:
            P = np.array(a['anello']); b = bad(P[:, 0], P[:, 1]); out[('a', ai)] = set(np.where(b)[0])
    P = np.array([p[:2] for p in d['sentiero']['punti']]); out[('s', 0)] = set(np.where(bad(P[:, 0], P[:, 1]))[0])
    return out
o = viol(carica(None), 'orig'); f = viol(carica('fase1_b.obj.state.pkl'), 'fin')
for k in f:
    new = f[k] - o.get(k, set())
    if new: print(k, 'nuovi punti in ostacoli:', sorted(new)[:12], 'tot', len(new), '| già prima:', len(o.get(k, set())))
print('ok')
