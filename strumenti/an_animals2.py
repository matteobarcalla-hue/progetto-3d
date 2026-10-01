import pickle, numpy as np, collections, sys
sys.path.insert(0,'tools'); from components import components
from scipy.spatial import cKDTree
V, objs, mtllib, header = pickle.load(open('orig.pkl','rb'))
AM = ('fur_','feather_','beak_')
tot = collections.Counter()
for o in objs:
    F = [np.array(f)-1 for f in o['faces']]
    if not F: continue
    lab = components(F)
    mats = np.array(o['mats'])
    comps = collections.defaultdict(list)
    for i,l in enumerate(lab): comps[l].append(i)
    anim = []
    for l, idx in comps.items():
        ms = collections.Counter(mats[idx])
        if any(m.startswith(AM) for m in ms):
            vs = np.unique(np.concatenate([F[i] for i in idx])); p = V[vs]
            anim.append((p.min(0), p.max(0), ms, len(idx)))
    if not anim: continue
    # group components into animals by bbox-center proximity
    c = np.array([(a[0]+a[1])/2 for a in anim])
    t = cKDTree(c); pairs = t.query_pairs(0.9)
    import scipy.sparse as sp, scipy.sparse.csgraph as cg
    n=len(anim); A = sp.coo_matrix((np.ones(len(pairs)), ([p[0] for p in pairs],[p[1] for p in pairs])), shape=(n,n))
    k, g = cg.connected_components(A, directed=False)
    dims = collections.Counter()
    for gi in range(k):
        mem = [anim[i] for i in range(n) if g[i]==gi]
        lo = np.min([m[0] for m in mem],0); hi = np.max([m[1] for m in mem],0)
        d = hi-lo; L = max(d[0], d[2]); H = d[1]
        dims[(round(L*2)/2, round(H*2)/2)] += 1
    print(f"{o['name']:22s} comps={n:4d} animali~{k:4d}  dims(L,H)={sorted(dims.items())[:12]}")
    tot[o['name']] = k
print('TOTALE ~', sum(tot.values()))
