import sys, numpy as np, collections
sys.path.insert(0, 'tools')
from stato import carica
from scipy.spatial import cKDTree
OGG = ('Alberi', 'Alberi_Nuovi', 'Alberi_Aree_Nuove', 'Alberi_Infittimento')
CH = {'tree_green', 'tree_light', 'tree_dark', 'tree_autumn', 'tree_olive', 'conifer', 'cypress', 'tree_bosco', 'hedge', 'vine', 'reed', 'lavender'}
for f in sys.argv[1:]:
    m = carica(f); d = []
    for nm in OGG:
        o = m.obj(nm); cs = m.comps(nm)
        pv = lambda c: collections.Counter(o['mats'][fi] for fi in c['faces']).most_common(1)[0][0]
        tr = [c for c in cs if pv(c) == 'trunk_brown']; fo = [c for c in cs if pv(c) in CH]
        FL = np.array([c['lo'] for c in fo]); FH = np.array([c['hi'] for c in fo]); kd = cKDTree(((FL + FH) / 2)[:, [0, 2]])
        for t in tr:
            ce = (t['lo'] + t['hi']) / 2
            ks = [k for k in kd.query_ball_point(ce[[0, 2]], 12.0) if FL[k][0] - 0.3 <= t['hi'][0] and t['lo'][0] <= FH[k][0] + 0.3 and FL[k][2] - 0.3 <= t['hi'][2] and t['lo'][2] <= FH[k][2] + 0.3 and FH[k][1] > t['lo'][1] + 1.0]
            if ks: d.append(t['hi'][1] - max(FH[k][1] for k in ks))
    d = np.array(d)
    print(f, 'tronchi con chioma', len(d), 'che spuntano sopra la chioma: >0,3 m %d, >1 m %d, >2 m %d' % ((d > 0.3).sum(), (d > 1).sum(), (d > 2).sum()))
