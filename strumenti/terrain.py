"""Terreno come griglia regolare: vertice (i,j) -> x=0.9*(i+I0), z=0.5+0.9*(j+J0).
H[i,j] quota vertici; M[i,j] indice materiale della cella (i..i+1, j..j+1), -1 = buco (grotte)."""
import numpy as np
S = 0.9
def coords(I0, J0, NI, NJ):
    x = S * (np.arange(NI) + I0); z = 0.5 + S * (np.arange(NJ) + J0)
    return x, z
def to_object(H, M, mats, I0, J0, V, name='Terreno'):
    """Aggiunge i vertici a V (lista/array) e restituisce l'oggetto; vertici separati per materiale."""
    NI, NJ = H.shape
    x, z = coords(I0, J0, NI, NJ)
    faces = []; fm = []; newv = []
    base = len(V)
    for k in np.argsort(mats):
        ci, cj = np.nonzero(M == k)
        if len(ci) == 0: continue
        corners = [(ci, cj), (ci, cj + 1), (ci + 1, cj + 1), (ci + 1, cj)]
        keys = np.concatenate([a * NJ + b for a, b in corners])
        uk, inv = np.unique(keys, return_inverse=True)
        vi, vj = uk // NJ, uk % NJ
        P = np.stack([x[vi], H[vi, vj], z[vj]], 1)
        idx = inv.reshape(4, -1).T + base + len(newv) + 1
        newv.extend(P.tolist())
        faces.extend(idx.tolist()); fm.extend([mats[k]] * len(ci))
    V = np.concatenate([np.asarray(V), np.array(newv)]) if len(newv) else V
    return V, dict(name=name, faces=faces, mats=fm, smooth=[True] * len(faces))
