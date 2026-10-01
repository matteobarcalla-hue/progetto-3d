import pickle, numpy as np, collections, ast, sys
sys.path.insert(0,'tools'); from components import components
V, objs, mtllib, header = pickle.load(open('orig.pkl','rb'))
O = {o['name']: o for o in objs}
a = O['Animali']; F = [np.array(f)-1 for f in a['faces']]
lab = components(F)
print('components', lab.max()+1)
mats = np.array(a['mats'])
cent=[]; 
for c in range(lab.max()+1):
    idx = np.where(lab==c)[0]; vs = np.unique(np.concatenate([F[i] for i in idx])); p=V[vs]
    cent.append((p[:,0].mean(), p[:,2].mean(), p[:,1].min(), p[:,1].max(), np.ptp(p[:,0]), np.ptp(p[:,2]), len(idx), collections.Counter(mats[idx]).most_common(2)))
print('mats', collections.Counter(a['mats']))
# cluster components by proximity (1.5 m) to get animals
C = np.array([[c[0], c[1]] for c in cent])
from scipy.cluster.hierarchy import fcluster, linkage
Z = linkage(C, 'single'); cl = fcluster(Z, 1.2, 'distance')
print('animal clusters (1.2m)', cl.max())
src=open('kit.py').read().split('\n')[30]
d=ast.literal_eval(src.split('=',1)[1].strip())
K = np.array([[x['x'], x['z']] for x in d['animali']])
from scipy.spatial import cKDTree
cc = np.array([C[cl==k].mean(0) for k in range(1, cl.max()+1)])
dist, _ = cKDTree(cc).query(K)
print('kit animals: dist to nearest OBJ animal cluster: median %.2f, <2m: %d / %d' % (np.median(dist), (dist<2).sum(), len(K)))
d2, _ = cKDTree(K).query(cc)
print('OBJ clusters with kit animal within 2m:', (d2<2).sum(), '/', len(cc))
far = cc[d2>=2]; print('OBJ clusters without kit animal (first 20):', np.round(far[:20],1).tolist())
print(d['animali'][:3])
