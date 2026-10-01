import sys, numpy as np, collections
sys.path.insert(0, 'tools')
from stato import carica
from scipy.spatial import cKDTree
import scipy.sparse as sp, scipy.sparse.csgraph as cg
m = carica('fase1_d.obj.state.pkl')
def cluster(nm, gap=0.35):
    o = m.obj(nm); cs = m.comps(nm)
    lo = np.array([c['lo'] for c in cs]); hi = np.array([c['hi'] for c in cs])
    n = len(cs); rows = []; cols = []
    # bbox che si toccano (in 3D) entro gap
    order = np.argsort(lo[:, 0])
    for a in range(n):
        for b in range(a + 1, n):
            if np.all(lo[a] - gap <= hi[b]) and np.all(lo[b] - gap <= hi[a]): rows.append(a); cols.append(b)
    A = sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    k, g = cg.connected_components(A, directed=False)
    out = []
    for gi in range(k):
        mem = [cs[i] for i in np.where(g == gi)[0]]
        L = np.min([c['lo'] for c in mem], 0); Hh = np.max([c['hi'] for c in mem], 0)
        mats = collections.Counter(o['mats'][f] for c in mem for f in c['faces'])
        out.append(dict(lo=L, hi=Hh, nf=sum(len(c['faces']) for c in mem), mats=mats, n=len(mem)))
    return out
for nm in ('Villaggio_Altopiano', 'Porto', 'Borgo_Basso'):
    cl = cluster(nm)
    big = [c for c in cl if (c['hi'][1] - c['lo'][1]) > 4 and max(c['hi'][0] - c['lo'][0], c['hi'][2] - c['lo'][2]) > 4]
    print('==', nm, 'gruppi', len(cl), 'grandi', len(big))
    for c in sorted(big, key=lambda c: -c['nf'])[:14]:
        d = c['hi'] - c['lo']
        print('  c=(%.1f,%.1f) dim=(%.1f x %.1f x %.1f) y0=%.1f facce %d %s' % ((c['lo'][0]+c['hi'][0])/2, (c['lo'][2]+c['hi'][2])/2, d[0], d[2], d[1], c['lo'][1], c['nf'], c['mats'].most_common(4)))
