import pickle, numpy as np, collections, sys
sys.path.insert(0,'tools'); from components import components
V, objs, mtllib, header = pickle.load(open('orig.pkl','rb'))
x0,x1,z0,z1 = map(float, sys.argv[1:5]); names = sys.argv[5].split(',') if len(sys.argv)>5 else None
minf = int(sys.argv[6]) if len(sys.argv)>6 else 1
for o in objs:
    if names and o['name'] not in names: continue
    if o['name'] in ('Terreno',): continue
    F=[np.array(f)-1 for f in o['faces']]; lab=components(F); mats=np.array(o['mats'])
    rows=[]
    for c in range(lab.max()+1):
        idx=np.where(lab==c)[0]; vs=np.unique(np.concatenate([F[i] for i in idx])); p=V[vs]
        lo=p.min(0); hi=p.max(0); ce=(lo+hi)/2
        if x0<=ce[0]<=x1 and z0<=ce[2]<=z1 and len(idx)>=minf:
            rows.append((ce[0],ce[2],lo,hi,len(idx),collections.Counter(mats[idx]).most_common(3)))
    if rows:
        print('==', o['name'], len(rows), 'componenti')
        for r in sorted(rows, key=lambda r:(-r[4]))[:40]:
            print('  c=(%.1f,%.1f) X[%.1f,%.1f] Y[%.1f,%.1f] Z[%.1f,%.1f] f=%d %s' % (r[0],r[1],r[2][0],r[3][0],r[2][1],r[3][1],r[2][2],r[3][2],r[4],r[5]))
