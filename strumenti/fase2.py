"""Fase 2: parte dallo stato finale della fase 1. Uso: python fase2.py stato_fase1.pkl out.obj moduli..."""
import sys, os, time, json, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
print('scritto', out, n, 'vertici')
