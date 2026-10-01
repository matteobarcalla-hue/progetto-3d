import sys, numpy as np, pickle, time, collections
sys.path.insert(0, 'tools'); import objio
t=time.time(); V, objs, mtllib, header = objio.load(sys.argv[1]); print('load', time.time()-t, 's')
print('verts', len(V), 'objs', len(objs), 'faces', sum(len(o['faces']) for o in objs))
allm=set()
for o in objs:
    fs=o['faces']; ids=np.unique(np.concatenate([np.array(f) for f in fs]))-1 if fs else np.array([],int)
    b=V[ids]; mats=collections.Counter(o['mats']); allm|=set(mats)
    ng=collections.Counter(len(f) for f in fs)
    print(f"{o['name']:24s} f={len(fs):7d} v={len(ids):7d} X[{b[:,0].min():7.1f},{b[:,0].max():7.1f}] Y[{b[:,1].min():6.1f},{b[:,1].max():6.1f}] Z[{b[:,2].min():7.1f},{b[:,2].max():7.1f}] ng={dict(ng)} mats={len(mats)} sm={sum(o['smooth'])}")
print('materials used', len(allm))
pickle.dump((V, objs, mtllib, header), open('orig.pkl','wb'), protocol=4)
