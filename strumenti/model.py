"""Stato di lavoro del modello: vertici, oggetti, griglia del terreno."""
import numpy as np, pickle, collections, copy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import objio, terrain
from components import components
I0, J0 = -339, -215
S = 0.9

class Model:
    def __init__(self, pkl='orig.pkl', grid='terrain_orig.npz'):
        V, objs, mtllib, header = pickle.load(open(pkl, 'rb'))
        self.V = V.copy(); self.objs = objs; self.header = header
        d = np.load(grid); self.H = d['H'].copy(); self.M = d['M'].copy(); self.mats = list(d['mats'])
        nan = np.isnan(self.H)
        if nan.any():   # vertici non usati (bordi delle grotte): quota del vicino valido più prossimo
            from scipy import ndimage
            idx = ndimage.distance_transform_edt(nan, return_distances=False, return_indices=True)
            self.H = self.H[idx[0], idx[1]]
        self.I0, self.J0 = I0, J0
        self._comp = {}
    # ------------------------------------------------ oggetti
    def obj(self, name):
        return next(o for o in self.objs if o['name'] == name)
    def has(self, name):
        return any(o['name'] == name for o in self.objs)
    def comps(self, name):
        """lista di componenti: dict(faces=[idx], lo, hi, verts)"""
        if name in self._comp: return self._comp[name]
        o = self.obj(name); F = [np.array(f) - 1 for f in o['faces']]
        out = []
        if F:
            lab = components(F)
            groups = collections.defaultdict(list)
            for i, l in enumerate(lab): groups[l].append(i)
            for l, idx in groups.items():
                vs = np.unique(np.concatenate([F[i] for i in idx]))
                P = self.V[vs]
                out.append(dict(faces=idx, verts=vs, lo=P.min(0), hi=P.max(0)))
        self._comp[name] = out
        return out
    def invalidate(self, name=None):
        if name: self._comp.pop(name, None)
        else: self._comp.clear()
    def select(self, test, names=None, exclude=('Terreno',)):
        """test(lo, hi) -> bool ; restituisce {oggetto: [facce]}"""
        sel = {}
        for o in self.objs:
            if o['name'] in exclude or (names and o['name'] not in names): continue
            fs = []
            for c in self.comps(o['name']):
                if test(c['lo'], c['hi']): fs += c['faces']
            if fs: sel[o['name']] = sorted(fs)
        return sel
    def sel_verts(self, sel):
        vs = []
        for name, fs in sel.items():
            o = self.obj(name)
            vs.append(np.unique(np.concatenate([np.array(o['faces'][i]) - 1 for i in fs])))
        return np.unique(np.concatenate(vs)) if vs else np.array([], int)
    def transform(self, sel, fn):
        """fn(P: (n,3)) -> (n,3) applicata ai vertici della selezione"""
        vs = self.sel_verts(sel)
        self.V[vs] = fn(self.V[vs])
        for name in sel: self.invalidate(name)
    def translate(self, sel, d):
        self.transform(sel, lambda P: P + np.asarray(d, float))
    def delete(self, sel):
        for name, fs in sel.items():
            o = self.obj(name); keep = np.ones(len(o['faces']), bool); keep[fs] = False
            for k in ('faces', 'mats', 'smooth'):
                o[k] = [x for x, kk in zip(o[k], keep) if kk]
            self.invalidate(name)
    def add_faces(self, name, P, faces, mats, smooth=False, after=None):
        """aggiunge geometria (P coordinate, faces indici 0-based locali) all'oggetto name (creato se manca)"""
        base = len(self.V)
        self.V = np.concatenate([self.V, np.asarray(P, float)])
        if not self.has(name):
            o = dict(name=name, faces=[], mats=[], smooth=[])
            if after and self.has(after):
                k = next(i for i, x in enumerate(self.objs) if x['name'] == after)
                self.objs.insert(k + 1, o)
            else:
                self.objs.append(o)
        o = self.obj(name)
        if isinstance(mats, str): mats = [mats] * len(faces)
        if isinstance(smooth, bool): smooth = [smooth] * len(faces)
        o['faces'] += [[base + i + 1 for i in f] for f in faces]
        o['mats'] += list(mats); o['smooth'] += list(smooth)
        self.invalidate(name)
    def copy_sel(self, sel, fn, target=None):
        """duplica la selezione trasformata da fn; target: nome oggetto (default stesso oggetto)"""
        for name, fs in sel.items():
            o = self.obj(name)
            vs = np.unique(np.concatenate([np.array(o['faces'][i]) - 1 for i in fs]))
            rm = {v: k for k, v in enumerate(vs)}
            P = fn(self.V[vs].copy())
            self.add_faces(target or name, P, [[rm[v - 1] for v in o['faces'][i]] for i in fs],
                           [o['mats'][i] for i in fs], [o['smooth'][i] for i in fs])
    # ------------------------------------------------ terreno
    def ij(self, x, z):
        return (np.asarray(x) / S - self.I0, (np.asarray(z) - 0.5) / S - self.J0)
    def xz(self, i, j):
        return (S * (np.asarray(i) + self.I0), 0.5 + S * (np.asarray(j) + self.J0))
    def height(self, x, z):
        """quota bilineare del terreno"""
        fi, fj = self.ij(x, z)
        i0 = np.clip(np.floor(fi).astype(int), 0, self.H.shape[0] - 2); j0 = np.clip(np.floor(fj).astype(int), 0, self.H.shape[1] - 2)
        a = np.clip(fi - i0, 0, 1); b = np.clip(fj - j0, 0, 1)
        H = self.H
        return (H[i0, j0] * (1 - a) * (1 - b) + H[i0 + 1, j0] * a * (1 - b) + H[i0, j0 + 1] * (1 - a) * b + H[i0 + 1, j0 + 1] * a * b)
    def height_tri(self, x, z):
        """quota esatta sulla superficie resa (quad diviso lungo la diagonale (i,j)-(i+1,j+1), come in Blender)"""
        fi, fj = self.ij(x, z)
        i0 = np.clip(np.floor(fi).astype(int), 0, self.H.shape[0] - 2); j0 = np.clip(np.floor(fj).astype(int), 0, self.H.shape[1] - 2)
        a = np.clip(fi - i0, 0, 1); b = np.clip(fj - j0, 0, 1); H = self.H
        h00 = H[i0, j0]; h01 = H[i0, j0 + 1]; h10 = H[i0 + 1, j0]; h11 = H[i0 + 1, j0 + 1]
        t1 = h00 + b * (h01 - h00) + a * (h11 - h01)
        t2 = h00 + a * (h10 - h00) + b * (h11 - h10)
        return np.where(b >= a, t1, t2)
    def mat_at(self, x, z):
        fi, fj = self.ij(x, z)
        k = self.M[np.clip(np.floor(fi).astype(int), 0, self.M.shape[0] - 1), np.clip(np.floor(fj).astype(int), 0, self.M.shape[1] - 1)]
        return np.where(k >= 0, np.array(self.mats + ['<buco>'])[k], '<buco>')
    def mat_index(self, name):
        if name not in self.mats: self.mats.append(name)
        return self.mats.index(name)
    def grid_xz(self):
        x = S * (np.arange(self.H.shape[0]) + self.I0); z = 0.5 + S * (np.arange(self.H.shape[1]) + self.J0)
        return np.meshgrid(x, z, indexing='ij')
    def cell_xz(self):
        x = S * (np.arange(self.M.shape[0]) + self.I0 + 0.5); z = 0.5 + S * (np.arange(self.M.shape[1]) + self.J0 + 0.5)
        return np.meshgrid(x, z, indexing='ij')
    # ------------------------------------------------ salvataggio
    def save(self, path, mtllib='castello_mappa_estesa.mtl'):
        V = self.V
        t = self.obj('Terreno')
        V2, tobj = terrain.to_object(self.H, self.M, self.mats, self.I0, self.J0, V)
        t['faces'], t['mats'], t['smooth'] = tobj['faces'], tobj['mats'], tobj['smooth']
        n = objio.save(path, V2, self.objs, mtllib, self.header)
        self.invalidate('Terreno')
        return n
