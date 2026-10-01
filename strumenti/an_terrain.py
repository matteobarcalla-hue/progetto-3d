import pickle, numpy as np, collections
V, objs, mtllib, header = pickle.load(open('orig.pkl','rb'))
O = {o['name']: o for o in objs}
t = O['Terreno']
F = np.array(t['faces']) - 1
ids = np.unique(F)
P = V[ids]
gx = np.round(P[:,0]/0.9, 3); gz = np.round((P[:,2]-0.5)/0.9, 3)
print('x on grid', np.mean(np.abs(gx-np.round(gx))<1e-3), 'z on grid', np.mean(np.abs(gz-np.round(gz))<1e-3))
off = ~((np.abs(gx-np.round(gx))<1e-3)&(np.abs(gz-np.round(gz))<1e-3))
print('off-grid verts', off.sum())
if off.sum(): print(P[off][:10])
key = collections.Counter(zip(np.round(gx).astype(int), np.round(gz).astype(int)))
mult = collections.Counter(key.values()); print('multiplicity of grid points', mult)
# first face orientation / vertex index order
print('face sample', F[:3], V[F[0]])
mats = collections.Counter(t['mats']); print(mats)
# face index -> material layout: are faces ordered by grid?
c = V[F].mean(axis=1)
print('face centers first', c[:5])
gi = np.round(gx).astype(int); gj = np.round(gz).astype(int)
order = np.lexsort((P[:,1], gj, gi))
from itertools import groupby
dy = []
k = np.stack([gi,gj],1)[order]; y = P[order,1]
same = np.all(k[1:]==k[:-1],axis=1)
d = (y[1:]-y[:-1])[same]
print('dup pairs', same.sum(), 'dy==0', np.sum(np.abs(d)<1e-4), 'dy>0.01', np.sum(d>0.01), 'max dy', d.max(), 'hist', np.histogram(d, bins=[0,1e-4,0.1,0.5,1,2,5,10,50,200])[0])
# how are faces connected? count faces per grid cell
cell = np.stack([np.floor(c[:,0]/0.9).astype(int), np.floor((c[:,2]-0.5)/0.9).astype(int)],1)
cc = collections.Counter(map(tuple,cell)); print('faces per cell', collections.Counter(cc.values()))
# vertical faces?
e1 = V[F[:,1]]-V[F[:,0]]; e2 = V[F[:,3]]-V[F[:,0]]
n = np.cross(e1, e2); n /= np.linalg.norm(n,axis=1)[:,None]+1e-12
print('normal y <0 (downward)', np.sum(n[:,1]<0), ' |ny|<0.2 (near vertical)', np.sum(np.abs(n[:,1])<0.2))
