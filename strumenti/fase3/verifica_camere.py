import sys, ast, pickle; sys.path.insert(0, 'tools')
import numpy as np
from stato import carica
from shapely.geometry import Polygon, Point
m = carica('fase3/finale.obj.state.pkl')
src = open('fase3/kit_v6.py').read().split('\n')
D = ast.literal_eval(next(l for l in src if l.startswith('DATI = ')).split('=', 1)[1].strip())
case = pickle.load(open('fase3/case_borghi.pkl', 'rb'))
P = [(Polygon(c['corpo']), c['y'] + c['alt']) for c in case]
pale = m.obj('Pale_Dolomitiche'); vs = np.unique(np.concatenate([np.asarray(f) for f in pale['faces']])) - 1; PP = m.V[vs]
for r in D['riprese'] + D.get('riprese_nuove', []):
    pts = r['punti']
    xs = []; 
    for a, b in zip(pts, pts[1:]):
        for t in np.linspace(0, 1, 20):
            x = a[0] + (b[0] - a[0]) * t; z = a[1] + (b[1] - a[1]) * t; h = a[2] + (b[2] - a[2]) * t
            xs.append((x, z, h, a[3]))
    minc = 1e9; dove = None
    for x, z, h, modo in xs:
        y = h if modo == 'a' else float(m.height(x, z)) + h
        g = y - float(m.height(x, z))
        for poly, top in P:
            if poly.distance(Point(x, z)) < 3: g = min(g, y - top)
        d = np.hypot(PP[:, 0] - x, PP[:, 2] - z)
        if d.min() < 5: g = min(g, y - PP[d < 5, 1].max())
        if g < minc: minc = g; dove = (round(x, 1), round(z, 1))
    print('%-24s distanza minima dal terreno/case/pale: %.1f m a %s' % (r['nome'], minc, dove))
