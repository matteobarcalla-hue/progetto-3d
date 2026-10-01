"""Fase 1: correzioni e riordino. Uso: python fase1.py out.obj [moduli...]"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import Model
import importlib
out = sys.argv[1]; mods = sys.argv[2:] or ['f_rocca']
m = Model()
LOG = {}
for name in mods:
    t = time.time()
    mod = importlib.import_module(name)
    LOG[name] = mod.run(m)
    print('== %s %.1fs' % (name, time.time() - t))
n = m.save(out)
import pickle
pickle.dump(dict(V=m.V, objs=m.objs, H=m.H, M=m.M, mats=m.mats), open(out + '.state.pkl', 'wb'))
json.dump(LOG, open(out + '.log.json', 'w'), indent=1, ensure_ascii=False)
print('scritto', out, n, 'vertici')
