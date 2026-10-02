"""tronchi senza chioma: nessuna chioma (o ramo fogliato) dello stesso oggetto attorno alla metà alta del tronco"""
import sys, numpy as np, collections
sys.path.insert(0, 'tools')
from stato import carica
from scipy.spatial import cKDTree
OGG = ('Alberi', 'Alberi_Nuovi', 'Alberi_Aree_Nuove', 'Alberi_Infittimento')
CH = {'tree_green', 'tree_light', 'tree_dark', 'tree_autumn', 'tree_olive', 'conifer', 'cypress', 'tree_bosco', 'hedge', 'vine', 'reed', 'lavender',
      'flower_red', 'flower_white', 'flower_yellow', 'flower_purple', 'crop_green', 'crop_gold'}
def spogli(f):
    m = carica(f); out = []
    for nm in OGG:
        o = m.obj(nm); cs = m.comps(nm)
        tr = [c for c in cs if collections.Counter(o['mats'][fi] for fi in c['faces']).most_common(1)[0][0] == 'trunk_brown']
        fo = [c for c in cs if collections.Counter(o['mats'][fi] for fi in c['faces']).most_common(1)[0][0] in CH]
        if not fo: continue
        FL = np.array([c['lo'] for c in fo]); FH = np.array([c['hi'] for c in fo])
        kd = cKDTree(((FL + FH) / 2)[:, [0, 2]])
        for t in tr:
            ce = (t['lo'] + t['hi']) / 2; h = t['hi'][1] - t['lo'][1]
            ymid = t['lo'][1] + 0.6 * h
            ok = False
            for k in kd.query_ball_point(ce[[0, 2]], 12.0):
                if (FL[k][0] - 0.3 <= t['hi'][0] and t['lo'][0] <= FH[k][0] + 0.3 and FL[k][2] - 0.3 <= t['hi'][2] and t['lo'][2] <= FH[k][2] + 0.3
                        and FH[k][1] >= ymid and FL[k][1] <= t['hi'][1] + 0.6):
                    ok = True; break
            if not ok: out.append((nm, ce, h))
    return out
A = spogli(sys.argv[1]); B = spogli(sys.argv[2])
Ac = np.array([a[1] for a in A])
print('tronchi senza chioma: partenza %d (alti fino a %.1f m), finale %d' % (len(A), max(a[2] for a in A), len(B)))
nuovi = [(nm, c, h) for nm, c, h in B if np.min(np.hypot(Ac[:, 0] - c[0], Ac[:, 2] - c[2])) > 1.0]
print('nuovi', len(nuovi))
for nm, c, h in nuovi: print('  NUOVO', nm, np.round(c, 1), 'alto %.1f' % h)
