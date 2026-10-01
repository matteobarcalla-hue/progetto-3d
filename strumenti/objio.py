"""Parser/writer OBJ minimale che conserva ordine di oggetti, gruppi di materiale e smoothing."""
import numpy as np, re, collections

class Obj:
    """objects: list of dict(name, faces: list of (mat, smooth, [idx...]) as arrays)"""
    pass

def load(path):
    V = []
    objs = []  # each: dict(name, faces=[list of index lists], mats=[], smooth=[])
    cur = None; mat = None; sm = False
    mtllib = None; header = []
    with open(path) as f:
        for line in f:
            c = line[:2]
            if c == 'v ':
                p = line.split(); V.append((float(p[1]), float(p[2]), float(p[3])))
            elif c == 'f ':
                idx = [int(t.split('/')[0]) for t in line.split()[1:]]
                cur['faces'].append(idx); cur['mats'].append(mat); cur['smooth'].append(sm)
            elif c == 'o ' or c == 'g ':
                cur = dict(name=line[2:].strip(), faces=[], mats=[], smooth=[]); objs.append(cur)
            elif line.startswith('usemtl'):
                mat = line.split(None, 1)[1].strip()
            elif c == 's ':
                sm = line.split()[1] not in ('off', '0')
            elif line.startswith('mtllib'):
                mtllib = line.split(None, 1)[1].strip()
            elif line.startswith('#') and cur is None:
                header.append(line.rstrip('\n'))
    return np.array(V, dtype=np.float64), objs, mtllib, header

def load_mtl(path):
    mats = collections.OrderedDict(); cur = None
    for line in open(path):
        s = line.strip()
        if s.startswith('newmtl'):
            cur = s.split(None, 1)[1]; mats[cur] = []
        elif cur is not None and s:
            mats[cur].append(s)
    return mats

def save(path, V, objs, mtllib='castello_mappa_estesa.mtl', header=None):
    """Scrive un OBJ: per ogni oggetto i vertici usati (in ordine di indice) poi le facce
    con usemtl/s solo quando cambiano. Formato numerico come l'originale (3 decimali)."""
    V = np.asarray(V)
    assert np.isfinite(V).all(), 'NaN/inf nei vertici'
    out = open(path, 'w', buffering=1 << 22)
    for h in (header or []):
        out.write(h + '\n')
    out.write('mtllib %s\n' % mtllib)
    base = 0
    for o in objs:
        if not o['faces']:
            continue
        out.write('o %s\n' % o['name'])
        groups = o.get('vgroups')   # opzionale: lista di (mat, smooth, [facce]) con vertici propri
        used = np.unique(np.concatenate([np.asarray(f) for f in o['faces']]))
        remap = np.full(used.max() + 1, -1, np.int64); remap[used] = np.arange(len(used)) + base + 1
        P = V[used - 1]
        out.write(''.join('v %.3f %.3f %.3f\n' % tuple(p) for p in P))
        cm, cs = None, None; buf = []
        for f, m, s in zip(o['faces'], o['mats'], o['smooth']):
            if m != cm:
                buf.append('usemtl %s\n' % m); cm = m
            if s != cs:
                buf.append('s 1\n' if s else 's off\n'); cs = s
            buf.append('f ' + ' '.join(str(remap[i]) for i in f) + '\n')
        out.write(''.join(buf))
        base += len(used)
    out.close()
    return base
