"""Controllo esatto delle compenetrazioni degli oggetti nuovi della fase 3 (Borgo_Altopiano, Borgo_Porto, Pale_Dolomitiche)
con tutti gli altri oggetti (esclusi terreno, acqua, mare, fondale, fasce del plastico):
- superfici che si intersecano: BVH dei triangoli, coppie di componenti con riquadri sovrapposti;
- per le Pale anche i vertici di altri oggetti chiusi dentro la roccia (raggio verso l'alto che incontra la roccia).
Uso: python conflitti4.py modello.obj.state.pkl [uscita.json]"""
import sys, json, collections
sys.path.insert(0, 'tools')
import numpy as np
import bpy  # noqa: F401  (rende disponibile mathutils)
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from stato import carica

m = carica(sys.argv[1])
NUOVI = ('Borgo_Altopiano', 'Borgo_Porto', 'Pale_Dolomitiche')
SALTA = ('Terreno', 'Base_Sezione', 'Acqua', 'Mare', 'Fondale_Esteso') + NUOVI

def tri(o, faces):
    T = []
    for fi in faces:
        f = o['faces'][fi]
        for k in range(1, len(f) - 1): T.append((f[0] - 1, f[k] - 1, f[k + 1] - 1))
    return T

def bvh(o, faces):
    T = tri(o, faces)
    vs = sorted({v for t in T for v in t}); rm = {v: i for i, v in enumerate(vs)}
    return BVHTree.FromPolygons([Vector(m.V[v]) for v in vs], [(rm[a], rm[b], rm[c]) for a, b, c in T], epsilon=0.0)

altri = []
for o in m.objs:
    if o['name'] in SALTA or not o['faces']: continue
    for c in m.comps(o['name']): altri.append((o['name'], o, c))
LO = np.array([c['lo'] for _, _, c in altri]); HI = np.array([c['hi'] for _, _, c in altri])
cache = {}
def bvh_altro(i):
    if i not in cache:
        nm, o, c = altri[i]; cache[i] = bvh(o, c['faces'])
    return cache[i]

R = collections.Counter(); es = collections.defaultdict(list)
for nm in NUOVI:
    if not m.has(nm): continue
    o = m.obj(nm)
    for c in m.comps(nm):
        ov = np.minimum(HI, c['hi']) - np.maximum(LO, c['lo'])
        k = np.nonzero(np.all(ov > 0.0, 1))[0]
        if not len(k): continue
        B = bvh(o, c['faces'])
        for i in k:
            hits = B.overlap(bvh_altro(i))
            if hits:
                on = altri[i][0]; oc = altri[i][2]
                R[(nm, on)] += 1
                if len(es[(nm, on)]) < 8: es[(nm, on)].append(dict(dove=np.round((oc['lo'] + oc['hi']) / 2, 1).tolist(), facce=len(oc['faces']), triangoli=len(hits)))
# vertici dentro la roccia delle Pale
dentro = collections.Counter(); es_d = collections.defaultdict(list)
if m.has('Pale_Dolomitiche'):
    o = m.obj('Pale_Dolomitiche'); allf = list(range(len(o['faces'])))
    B = bvh(o, allf)
    vs = np.unique(np.concatenate([np.asarray(f) for f in o['faces']])) - 1; P = m.V[vs]
    lo = P.min(0); hi = P.max(0)
    for i in np.nonzero(np.all((HI > lo) & (LO < hi), 1))[0]:
        on, oo, oc = altri[i]
        n_in = 0
        for v in m.V[oc['verts']]:
            if not (lo[0] < v[0] < hi[0] and lo[2] < v[2] < hi[2]): continue
            loc, nor, idx, d = B.ray_cast(Vector(v), Vector((0, 1, 0)))
            if loc is not None and nor.y > 0.5:                  # la prima superficie sopra è la faccia superiore della roccia: dentro
                n_in += 1
        if n_in >= 2:
            dentro[on] += 1
            if len(es_d[on]) < 8: es_d[on].append(dict(dove=np.round((oc['lo'] + oc['hi']) / 2, 1).tolist(), vertici_dentro=n_in))
print('superfici che si intersecano (componenti nuove / componenti di altri oggetti):', {'%s / %s' % k: v for k, v in R.items()} or 'nessuna')
for k, v in es.items(): print('  ', k, v[:4])
print('componenti di altri oggetti con vertici dentro la roccia delle Pale:', dict(dentro) or 'nessuna')
for k, v in es_d.items(): print('  ', k, v[:4])
if len(sys.argv) > 2:
    json.dump(dict(intersezioni={'%s / %s' % k: v for k, v in R.items()}, esempi={'%s / %s' % k: v for k, v in es.items()},
                   dentro_pale=dict(dentro), esempi_pale=dict(es_d)), open(sys.argv[2], 'w'), indent=1, ensure_ascii=False)
