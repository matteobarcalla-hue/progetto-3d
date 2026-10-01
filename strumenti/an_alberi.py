import sys, numpy as np, collections, pickle
sys.path.insert(0, 'tools')
from stato import carica
from scipy.spatial import cKDTree
import scipy.sparse as sp, scipy.sparse.csgraph as cg
m = carica('fase1_d.obj.state.pkl')
names = np.array(m.mats + ['<buco>'])[m.M]
trees = []
for nm in ('Alberi', 'Alberi_Nuovi'):
    o = m.obj(nm); cs = m.comps(nm)
    C = np.array([((c['lo'] + c['hi']) / 2)[[0, 2]] for c in cs])
    pairs = cKDTree(C).query_pairs(0.6)
    n = len(cs); A = sp.coo_matrix((np.ones(len(pairs)), ([p[0] for p in pairs], [p[1] for p in pairs])), shape=(n, n))
    k, g = cg.connected_components(A, directed=False)
    for gi in range(k):
        mem = [cs[i] for i in np.where(g == gi)[0]]
        lo = np.min([c['lo'] for c in mem], 0); hi = np.max([c['hi'] for c in mem], 0)
        nf = sum(len(c['faces']) for c in mem)
        mats = collections.Counter(o['mats'][f] for c in mem for f in c['faces'])
        trees.append(dict(obj=nm, lo=lo, hi=hi, nf=nf, mats=mats, comps=len(mem)))
print('alberi (gruppi):', len(trees), 'facce medie %.1f' % np.mean([t['nf'] for t in trees]))
print('per oggetto', collections.Counter(t['obj'] for t in trees))
print('componenti per albero', collections.Counter(t['comps'] for t in trees).most_common(6))
print('altezze p10/50/90', np.percentile([t['hi'][1] - t['lo'][1] for t in trees], [10, 50, 90]))
tipo = collections.Counter(max(t['mats'], key=lambda k: t['mats'][k] if k != 'trunk_brown' else -1) for t in trees)
print('tipo (materiale chioma principale)', tipo.most_common(12))
# densità per materiale del suolo sotto l'albero
cnt = collections.Counter()
for t in trees:
    c = (t['lo'] + t['hi']) / 2; i, j = m.ij(c[0], c[2]); i = int(i); j = int(j)
    if 0 <= i < names.shape[0] and 0 <= j < names.shape[1]: cnt[names[i, j]] += 1
area = collections.Counter(names.ravel())
for k_, v in cnt.most_common(12): print('  %-15s alberi %5d  area %7.0f m2  densità %.4f /m2 (1 ogni %.0f m2)' % (k_, v, area[k_] * 0.81, v / (area[k_] * 0.81), area[k_] * 0.81 / v))
pickle.dump(trees, open('alberi_gruppi.pkl', 'wb'))
