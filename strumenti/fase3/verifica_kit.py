import sys, ast, pickle; sys.path.insert(0, 'tools')
import numpy as np
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
src = open(sys.argv[1]).read().split('\n')
D = ast.literal_eval(next(l for l in src if l.startswith('DATI = ')).split('=', 1)[1].strip())
case = pickle.load(open('fase3/case_borghi.pkl', 'rb'))
from shapely import wkt
PALE = wkt.loads(pickle.load(open('fase3/pale_impronta.pkl', 'rb')))
U = unary_union([Polygon(c['corpo']).buffer(-0.2) for c in case] + [PALE])
tot = 0
for k, p in enumerate(D['percorsi']):
    P = [tuple(q[:2]) for q in p['punti']]
    L = LineString(P + [P[0]])
    inter = L.intersection(U).length
    if inter > 0.05:
        print('percorso %d attraversa case nuove o Pale per %.1f m' % (k, inter)); tot += 1
A = [a for a in D['animali'] if U.contains(__import__('shapely.geometry', fromlist=['Point']).Point(a['x'], a['z']))]
print('percorsi che attraversano case nuove o Pale:', tot, '; animali dentro case nuove o Pale:', len(A))
