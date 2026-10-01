"""Gruppi animali statici nell'OBJ (tutti gli oggetti) vs animali del kit."""
import pickle, numpy as np, collections, sys, ast, json
sys.path.insert(0,'tools'); from components import components
from scipy.spatial import cKDTree
import scipy.sparse as sp, scipy.sparse.csgraph as cg
src = sys.argv[1] if len(sys.argv) > 1 else 'orig.pkl'
V, objs, mtllib, header = pickle.load(open(src,'rb'))
AM = ('fur_','feather_','beak_','wool_')
groups = []
for o in objs:
    F = [np.array(f)-1 for f in o['faces']]
    if not F: continue
    lab = components(F); mats = np.array(o['mats'])
    comps = collections.defaultdict(list)
    for i,l in enumerate(lab): comps[l].append(i)
    anim = []
    for l, idx in comps.items():
        ms = collections.Counter(mats[idx])
        if any(m.startswith(AM) for m in ms):
            vs = np.unique(np.concatenate([F[i] for i in idx])); p = V[vs]
            anim.append((p.min(0), p.max(0), ms, idx))
    if not anim: continue
    c = np.array([(a[0]+a[1])/2 for a in anim])
    pairs = cKDTree(c).query_pairs(0.9)
    n = len(anim); A = sp.coo_matrix((np.ones(len(pairs)), ([p[0] for p in pairs],[p[1] for p in pairs])), shape=(n,n))
    k, g = cg.connected_components(A, directed=False)
    for gi in range(k):
        mem = [anim[i] for i in range(n) if g[i]==gi]
        lo = np.min([m[0] for m in mem],0); hi = np.max([m[1] for m in mem],0)
        ms = sum((m[2] for m in mem), collections.Counter())
        groups.append(dict(obj=o['name'], lo=lo.tolist(), hi=hi.tolist(), mats=dict(ms), faces=[int(f) for m in mem for f in m[3]]))
print('gruppi', len(groups), collections.Counter(g['obj'] for g in groups))
d = ast.literal_eval(open('kit.py').read().split('\n')[30].split('=',1)[1].strip())
K = np.array([[a['x'], a['z']] for a in d['animali']])
C = np.array([[(g['lo'][0]+g['hi'][0])/2, (g['lo'][2]+g['hi'][2])/2] for g in groups])
dist, idx = cKDTree(K).query(C)
print('gruppi OBJ con animale del kit entro 2 m:', (dist<2).sum(), 'entro 5 m:', (dist<5).sum(), '/', len(C))
by = collections.defaultdict(list)
for g, dd in zip(groups, dist): by[g['obj']].append(dd)
for k_, v in by.items(): print(' ', k_, len(v), 'entro 2m', sum(1 for x in v if x<2), 'mediana %.1f' % np.median(v))
dk, _ = cKDTree(C).query(K)
print('animali del kit con gruppo OBJ entro 2 m:', (dk<2).sum(), '/', len(K))
json.dump(groups, open('animal_groups.json','w'))
