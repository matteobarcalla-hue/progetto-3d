import sys, numpy as np, ast
sys.path.insert(0, 'tools')
from stato import carica
from occupancy import occupancy_fine
from an_kit import ESCL, d
m = carica('fase1_b.obj.state.pkl')
# chi occupa: rasterizzo per oggetto solo attorno ai punti
from PIL import Image, ImageDraw
def who(x, z):
    res = set()
    for o in m.objs:
        if o['name'] in ('Terreno','Base_Sezione','Mare') + ESCL: continue
        for c in m.comps(o['name']):
            if c['lo'][0]-0.5 <= x <= c['hi'][0]+0.5 and c['lo'][2]-0.5 <= z <= c['hi'][2]+0.5 and (c['hi'][0]-c['lo'][0])*(c['hi'][2]-c['lo'][2]) < 3000:
                res.add(o['name'])
    return res
for ri, idx in ((14, [48, 50]), (17, [0, 1, 3, 58, 59]), (19, [30, 34, 38, 42, 44]), (23, [50, 53, 57])):
    P = d['percorsi'][ri]['punti']
    print(ri, 'persone', d['percorsi'][ri]['persone'], 'n', len(P), 'primo', P[0])
    for k in idx: print('   ', k, P[k], who(*P[k]))
