import sys, os, pickle, json, time
sys.path.insert(0, 'tools')
from stato import carica
import importlib
st, out = sys.argv[1], sys.argv[2]; mods = sys.argv[3:]
m = carica(st)
LOG = {}
for name in mods:
    t = time.time()
    mod = importlib.import_module(name)
    LOG[name] = list(mod.run(m))
    print('== %s %.1fs' % (name, time.time() - t), flush=True)
n = m.save(out)
pickle.dump(dict(V=m.V, objs=m.objs, H=m.H, M=m.M, mats=m.mats, I0=m.I0, J0=m.J0), open(out + '.state.pkl', 'wb'))
json.dump(LOG, open(out + '.log.json', 'w'), indent=1, ensure_ascii=False)
print('scritto', out, n, 'vertici', sum(len(o['faces']) for o in m.objs), 'facce')
