"""Converte il Terreno in griglia: H (quote ai vertici), M (materiale per cella), holes, dup (split)."""
import pickle, numpy as np, collections
I0, I1, J0, J1 = -339, 302, -215, 265   # indici vertici: x=0.9*i, z=0.5+0.9*j
def gridify(V, t):
    F = np.array(t['faces']) - 1
    P = V[F]                                   # (nf,4,3)
    gi = np.round(P[:,:,0]/0.9).astype(int) - I0
    gj = np.round((P[:,:,2]-0.5)/0.9).astype(int) - J0
    NI, NJ = I1-I0+1, J1-J0+1
    H = np.full((NI, NJ), np.nan)
    H[gi.ravel(), gj.ravel()] = P[:,:,1].ravel()
    ci = gi.min(1); cj = gj.min(1)
    mats = sorted(set(t['mats'])); mi = {m:k for k,m in enumerate(mats)}
    M = np.full((NI-1, NJ-1), -1, int)
    M[ci, cj] = [mi[m] for m in t['mats']]
    # vertex-split map: count distinct vertex ids per grid point
    cnt = collections.defaultdict(set)
    for f, a, b in zip(F.ravel(), gi.ravel(), gj.ravel()):
        cnt[(a,b)].add(f)
    D = np.zeros((NI, NJ), int)
    for (a,b), s in cnt.items(): D[a,b] = len(s)
    # face winding sample
    return H, M, mats, D, F[0]
if __name__ == '__main__':
    V, objs, mtllib, header = pickle.load(open('orig.pkl','rb'))
    t = next(o for o in objs if o['name']=='Terreno')
    H, M, mats, D, f0 = gridify(V, t)
    print(H.shape, np.isnan(H).sum(), (M<0).sum(), mats, 'dup>1', (D>1).sum())
    np.savez_compressed('terrain_orig.npz', H=H, M=M, mats=np.array(mats), D=D)
