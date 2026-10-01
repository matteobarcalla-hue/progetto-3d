"""Elementi sospesi: componenti connesse non collegate al terreno (o all'acqua) tramite una catena di
contatti (distanza <= SOGLIA) o compenetrazioni. Uso: venv/bin/python floating.py modello.obj [soglia]"""
import sys, os, numpy as np, collections, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils.bvhtree import BVHTree
import objio
from components import components
import scipy.sparse as sp, scipy.sparse.csgraph as cg
path = sys.argv[1]; SOGLIA = float(sys.argv[2]) if len(sys.argv) > 2 else 0.15
SUPPORTI = ('Terreno', 'Mare', 'Acqua', 'Base_Sezione')
t0 = time.time()
V, objs, _, _ = objio.load(path)
polys = []; comp = []; cobj = []
cid = 0
for o in objs:
    F = [list(np.array(f) - 1) for f in o['faces']]
    if o['name'] in SUPPORTI:
        lab = np.zeros(len(F), int)
    else:
        lab = components([np.array(f) for f in F])
    polys += F; comp += list(lab + cid); cobj += [o['name']] * (lab.max() + 1)
    cid += lab.max() + 1
comp = np.array(comp); NC = cid
supp = np.array([n in SUPPORTI for n in cobj])
print('componenti', NC, 'load', round(time.time() - t0, 1))
bvh = BVHTree.FromPolygons([tuple(v) for v in V], polys, all_triangles=False, epsilon=0.0)
cpolys = collections.defaultdict(list)
for k, c in enumerate(comp): cpolys[c].append(k)
lo = np.zeros((NC, 3)); hi = np.zeros((NC, 3)); cverts = {}
for c, ks in cpolys.items():
    vs = np.unique(np.concatenate([polys[k] for k in ks])); cverts[c] = vs
    lo[c] = V[vs].min(0); hi[c] = V[vs].max(0)
E = set()
# 0) appoggio sul terreno per quota: un vertice sotto (terreno + SOGLIA) collega al suolo
tobj = next(o for o in objs if o['name'] == 'Terreno')
TF = np.array(tobj['faces']) - 1; TP = V[TF]
ti = np.round(TP[:, :, 0].min(1) / 0.9).astype(int); tj = np.round((TP[:, :, 2].min(1) - 0.5) / 0.9).astype(int)
ti0, tj0 = ti.min(), tj.min()
HG = np.full((ti.max() - ti0 + 2, tj.max() - tj0 + 2), np.nan)
for k in range(4):
    gi = np.round(TP[:, k, 0] / 0.9).astype(int) - ti0; gj = np.round((TP[:, k, 2] - 0.5) / 0.9).astype(int) - tj0
    HG[gi, gj] = TP[:, k, 1]
HG = np.where(np.isnan(HG), -1e9, HG)
def hterr(x, z):
    fi = x / 0.9 - ti0; fj = (z - 0.5) / 0.9 - tj0
    i = np.clip(np.floor(fi).astype(int), 0, HG.shape[0] - 2); j = np.clip(np.floor(fj).astype(int), 0, HG.shape[1] - 2)
    a = np.clip(fi - i, 0, 1); b = np.clip(fj - j, 0, 1)
    return HG[i, j] * (1 - a) * (1 - b) + HG[i + 1, j] * a * (1 - b) + HG[i, j + 1] * (1 - a) * b + HG[i + 1, j + 1] * a * b
TERR = next(c for c in range(NC) if cobj[c] == 'Terreno')
E = set()
for c in range(NC):
    if supp[c]: continue
    P = V[cverts[c]]
    if np.any(P[:, 1] <= hterr(P[:, 0], P[:, 2]) + SOGLIA):
        E.add((min(c, TERR), max(c, TERR)))
print('appoggi sul terreno', len(E), flush=True)
# 1) contatti: vertici più bassi e un campione degli altri vicino ad altra geometria
for c in range(NC):
    if supp[c]: continue
    P = V[cverts[c]]
    order = np.argsort(P[:, 1]); sel = np.concatenate([order[:16], order[16::max(1, len(order) // 16)]])
    found = set()
    for p in P[sel]:
        for loc, nor, idx, dist in bvh.find_nearest_range(tuple(p), SOGLIA):
            d = comp[idx]
            if d != c and d not in found:
                found.add(d); E.add((min(c, d), max(c, d)))
                if supp[d]: break
        if len(found) >= 4 or any(supp[d] for d in found): break
print('contatti', len(E), round(time.time() - t0, 1), flush=True)
# 2) grafo dei contatti -> componenti collegate al suolo; poi compenetrazioni solo per le altre
def ground_set(E):
    rows = [a for a, b in E] + [c for c in range(NC) if supp[c]]
    cols = [b for a, b in E] + [NC] * int(supp.sum())
    A = sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(NC + 1, NC + 1))
    k, lab = cg.connected_components(A, directed=False)
    return lab
cache = {}
def cb(c):
    if c not in cache:
        vs = cverts[c]; rm = {v: i for i, v in enumerate(vs)}
        cache[c] = BVHTree.FromPolygons([tuple(V[v]) for v in vs], [[rm[v] for v in polys[k]] for k in cpolys[c]], all_triangles=False)
    return cache[c]
tested = set()
for it in range(6):
    lab = ground_set(E); ground = lab[NC]
    cand = [c for c in range(NC) if lab[c] != ground]
    added = 0
    for c in cand:
        ov = np.where((hi[:, 0] >= lo[c, 0]) & (lo[:, 0] <= hi[c, 0]) & (hi[:, 1] >= lo[c, 1]) & (lo[:, 1] <= hi[c, 1]) & (hi[:, 2] >= lo[c, 2]) & (lo[:, 2] <= hi[c, 2]))[0]
        for d in ov:
            if d == c or supp[d] or lab[d] == lab[c]: continue
            key = (min(c, d), max(c, d))
            if key in tested: continue
            tested.add(key)
            if cb(c).overlap(cb(d)):
                E.add(key); added += 1
    print('iterazione', it, 'candidati', len(cand), 'nuovi archi', added, round(time.time() - t0, 1), flush=True)
    if not added: break
lab = ground_set(E); ground = lab[NC]
flo = [c for c in range(NC) if lab[c] != ground]
groups = collections.defaultdict(list)
for c in flo: groups[lab[c]].append(c)
out = []
for g, cs in groups.items():
    l = lo[cs].min(0); h = hi[cs].max(0)
    obs = collections.Counter(cobj[c] for c in cs)
    nf = sum(len(cpolys[c]) for c in cs)
    out.append(dict(oggetti=dict(obs), facce=nf, centro=[round(float(v), 2) for v in (l + h) / 2], y_min=round(float(l[1]), 2), dim=[round(float(v), 2) for v in h - l]))
print('tempo', round(time.time() - t0, 1))
cnt = collections.Counter(next(iter(o['oggetti'])) for o in out)
print('ELEMENTI SOSPESI:', len(out), dict(cnt))
json.dump(out, open(path + '.sospesi.json', 'w'), indent=0)
