"""Controlli numerici su un OBJ (senza Blender): validità, peso, terreno, elementi sospesi.
Uso: python checks.py modello.obj modello.mtl [--sospesi]"""
import sys, os, numpy as np, collections, pickle, json
sys.path.insert(0, os.path.dirname(__file__))
import objio
from components import components
from scipy.spatial import cKDTree
path, mtl = sys.argv[1], sys.argv[2]
R = {}
# ---- validità grezza dal file
nv = 0; bad_idx = 0; nan = 0; used_m = set(); nf = 0
with open(path) as f:
    for line in f:
        if line.startswith('v '):
            nv += 1
            p = line.split()[1:4]
            if any(t.lower() in ('nan', 'inf', '-inf') for t in p): nan += 1
        elif line.startswith('f '):
            nf += 1
            for t in line.split()[1:]:
                i = int(t.split('/')[0])
                if i < 1 or i > nv: bad_idx += 1
        elif line.startswith('usemtl'):
            used_m.add(line.split(None, 1)[1].strip())
defined = set(objio.load_mtl(mtl).keys())
R['vertici'] = nv; R['facce'] = nf; R['indici_non_validi'] = bad_idx; R['NaN'] = nan
R['materiali_usati'] = len(used_m); R['materiali_non_definiti'] = sorted(used_m - defined)
R['MB'] = round(os.path.getsize(path) / 1e6, 2)
V, objs, _, _ = objio.load(path)
R['oggetti'] = len(objs)
R['facce_per_oggetto'] = {o['name']: len(o['faces']) for o in objs}
# ---- terreno
t = next(o for o in objs if o['name'] == 'Terreno')
F = np.array(t['faces']) - 1; P = V[F]
n = np.cross(P[:, 1] - P[:, 0], P[:, 3] - P[:, 0])
R['terreno_normali_verso_basso'] = int(np.sum(n[:, 1] <= 0))
xs = P[:, :, 0].min(1); zs = P[:, :, 2].min(1)
ci = np.round(xs / 0.9).astype(int); cj = np.round((zs - 0.5) / 0.9).astype(int)
NI = ci.max() - ci.min() + 1; NJ = cj.max() - cj.min() + 1
R['terreno_celle_mancanti(grotte)'] = int(NI * NJ - len(F))
R['estensione_X'] = [float(V[:, 0].min()), float(V[:, 0].max())]
R['estensione_Z'] = [float(V[:, 2].min()), float(V[:, 2].max())]
json.dump(R, open(path + '.checks.json', 'w'), indent=1, ensure_ascii=False)
for k, v in R.items():
    if k != 'facce_per_oggetto': print(k, v)
